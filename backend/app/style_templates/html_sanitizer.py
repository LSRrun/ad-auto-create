import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser


STYLE_FIELDS = {
    "brand",
    "eyebrow",
    "headline",
    "productName",
    "productImage",
    "description",
    "price",
    "feature1",
    "feature2",
    "feature3",
    "cta",
}
ALLOWED_TAGS = {
    "html", "head", "body", "title", "meta", "style", "article", "section", "main", "header", "footer",
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6", "small", "strong", "b", "em", "i",
    "ul", "ol", "li", "img", "figure", "figcaption", "br", "hr",
}
VOID_TAGS = {"meta", "img", "br", "hr"}
DROP_CONTENT_TAGS = {"script", "iframe", "object", "form", "button", "textarea", "select", "option", "svg", "math", "canvas", "video", "audio"}
DROP_VOID_TAGS = {"embed", "input", "link"}
GLOBAL_ATTRS = {"class", "id", "style", "role", "aria-label", "aria-hidden", "title"}
TAG_ATTRS = {
    "img": {"src", "alt", "width", "height"},
    "meta": {"charset", "name", "content"},
}
SAFE_PROTOCOLS = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,", "{{productImage}}")


@dataclass
class SanitizedDocument:
    html: str
    nodes: list[dict]
    bindings: dict[str, str]
    warnings: list[str]
    palette: dict[str, str]


def sanitize_css(value: str) -> str:
    cleaned = re.sub(r"@import[^;]*;?", "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"url\s*\(\s*(['\"]?)(?!data:image/(?:png|jpeg|webp);base64,)[^)]+\)", "none", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?:expression|javascript|vbscript|behavior|-moz-binding)\s*[:(][^;}]*(?:[;}]|$)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"position\s*:\s*fixed", "position:absolute", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"z-index\s*:\s*[0-9]{5,}", "z-index:100", cleaned, flags=re.IGNORECASE)
    return cleaned[:100_000]


def _safe_attr(tag: str, name: str, value: str) -> tuple[str, str] | None:
    lowered = name.lower()
    if lowered.startswith("on") or lowered in {"srcdoc", "href", "action", "formaction"}:
        return None
    if lowered.startswith("data-"):
        if lowered not in {"data-ad-field", "data-template-node"}:
            return None
    elif lowered not in GLOBAL_ATTRS and lowered not in TAG_ATTRS.get(tag, set()):
        return None
    if lowered == "data-ad-field" and value not in STYLE_FIELDS:
        return None
    if lowered == "style":
        value = sanitize_css(value)
    if lowered == "src":
        normalized = value.strip()
        if not any(normalized.startswith(prefix) for prefix in SAFE_PROTOCOLS):
            return None
        value = normalized
    return lowered, value


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output: list[str] = []
        self.nodes: list[dict] = []
        self.bindings: dict[str, str] = {}
        self.warnings: list[str] = []
        self.stack: list[tuple[str, str | None]] = []
        self.drop_depth = 0
        self.node_index = 0
        self.in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.drop_depth:
            self.drop_depth += 1
            return
        if tag in DROP_CONTENT_TAGS:
            self.drop_depth = 1
            self.warnings.append(f"已移除不安全标签 <{tag}>")
            return
        if tag in DROP_VOID_TAGS:
            self.warnings.append(f"已移除不安全标签 <{tag}>")
            return
        if tag not in ALLOWED_TAGS:
            self.stack.append((tag, None))
            self.warnings.append(f"已移除不支持的标签 <{tag}>")
            return
        attr_map: dict[str, str] = {}
        for name, raw_value in attrs:
            safe = _safe_attr(tag, name, raw_value or "")
            if safe:
                attr_map[safe[0]] = safe[1]
        node_id = None
        if tag not in {"html", "head", "body", "title", "meta", "style", "br", "hr"}:
            self.node_index += 1
            node_id = f"node-{self.node_index}"
            attr_map["data-template-node"] = node_id
            field = attr_map.get("data-ad-field")
            if field and field not in self.bindings:
                self.bindings[field] = node_id
            self.nodes.append({"id": node_id, "tag": tag, "text": "", "class": attr_map.get("class", ""), "field": field})
        rendered_attrs = "".join(
            f' {html.escape(name, quote=True)}="{html.escape(value, quote=True)}"'
            for name, value in attr_map.items()
        )
        self.output.append(f"<{tag}{rendered_attrs}>")
        if tag not in VOID_TAGS:
            self.stack.append((tag, node_id))
        self.in_style = tag == "style"

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.drop_depth:
            self.drop_depth -= 1
            return
        if tag not in ALLOWED_TAGS:
            if self.stack and self.stack[-1][0] == tag:
                self.stack.pop()
            return
        if tag not in VOID_TAGS:
            self.output.append(f"</{tag}>")
            if self.stack:
                self.stack.pop()
        if tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.drop_depth:
            return
        value = sanitize_css(data) if self.in_style else html.escape(data)
        self.output.append(value)
        if not self.in_style and self.stack:
            node_id = self.stack[-1][1]
            if node_id:
                for node in self.nodes:
                    if node["id"] == node_id:
                        node["text"] = (node["text"] + data).strip()[:200]
                        break

    def handle_comment(self, data: str) -> None:
        return


class _BindingApplier(HTMLParser):
    def __init__(self, node_to_field: dict[str, str]):
        super().__init__(convert_charrefs=True)
        self.node_to_field = node_to_field
        self.output: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name: value or "" for name, value in attrs if name != "data-ad-field"}
        node_id = attr_map.get("data-template-node")
        if node_id in self.node_to_field:
            attr_map["data-ad-field"] = self.node_to_field[node_id]
        rendered = "".join(f' {html.escape(name, quote=True)}="{html.escape(value, quote=True)}"' for name, value in attr_map.items())
        self.output.append(f"<{tag}{rendered}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag not in VOID_TAGS:
            self.output.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.output.append(html.escape(data))


def _infer_bindings(nodes: list[dict], existing: dict[str, str]) -> dict[str, str]:
    bindings = dict(existing)
    used = set(bindings.values())

    def choose(field: str, predicate) -> None:
        if field in bindings:
            return
        for node in nodes:
            if node["id"] not in used and predicate(node):
                bindings[field] = node["id"]
                used.add(node["id"])
                return

    choose("productImage", lambda node: node["tag"] in {"img", "figure"} or "product" in node["class"].lower())
    choose("brand", lambda node: any(word in node["class"].lower() for word in ("brand", "logo")))
    choose("eyebrow", lambda node: any(word in node["class"].lower() for word in ("eyebrow", "kicker", "overline")))
    choose("headline", lambda node: node["tag"] == "h1")
    choose("headline", lambda node: node["tag"] in {"h2", "h3"})
    choose("productName", lambda node: node["tag"] in {"h2", "h3", "h4"})
    choose("price", lambda node: bool(re.search(r"(?:¥|\bRMB\b|元|￥|\$)\s*[0-9]", node["text"], re.IGNORECASE)))
    choose("cta", lambda node: any(word in node["text"] for word in ("立即", "了解", "购买", "咨询", "查看")))
    choose("description", lambda node: node["tag"] == "p" and len(node["text"]) >= 12)
    for index in range(1, 4):
        choose(f"feature{index}", lambda node: node["tag"] == "li")
    return bindings


def apply_bindings(document: str, bindings: dict[str, str]) -> str:
    node_to_field = {node_id: field for field, node_id in bindings.items() if field in STYLE_FIELDS}
    parser = _BindingApplier(node_to_field)
    parser.feed(document)
    return "".join(parser.output)


def _extract_palette(document: str) -> dict[str, str]:
    colors = []
    for color in re.findall(r"#[0-9a-fA-F]{6}\b", document):
        normalized = color.upper()
        if normalized not in colors:
            colors.append(normalized)
    defaults = ["#F3F0EA", "#FFFFFF", "#20211F", "#826B4D"]
    values = (colors + defaults)[:4]
    return {"background": values[0], "surface": values[1], "text": values[2], "accent": values[3]}


def sanitize_html(document: str) -> SanitizedDocument:
    parser = _Sanitizer()
    parser.feed(document)
    sanitized = "".join(parser.output)
    bindings = _infer_bindings(parser.nodes, parser.bindings)
    bound_html = apply_bindings(sanitized, bindings)
    if "productImage" not in bindings:
        parser.warnings.append("未识别到商品图容器，请手动映射")
    if "headline" not in bindings:
        parser.warnings.append("未识别到广告大标题，请手动映射")
    return SanitizedDocument(
        html=bound_html,
        nodes=parser.nodes,
        bindings=bindings,
        warnings=list(dict.fromkeys(parser.warnings)),
        palette=_extract_palette(bound_html),
    )
