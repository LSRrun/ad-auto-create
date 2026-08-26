import asyncio
import ipaddress
import re
import socket
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from .schemas import CreateMediaPlanRequest, ResearchEvidence


SEARCH_URL = "https://html.duckduckgo.com/html/"
TIMEOUT = httpx.Timeout(12.0, connect=6.0)
MAX_PAGE_BYTES = 600_000


CURATED_EVIDENCE = [
    {
        "topic": "campaign_structure",
        "title": "How to set up an ad campaign in TikTok Ads Manager",
        "url": "https://ads.tiktok.com/resources/help/article/campaign-set-up",
        "publisher": "TikTok for Business",
        "summary": "官方将广告组织为 Campaign、Ad Group 和 Ad 三层，计划层设置目标和预算。",
        "supports": ["campaigns", "ad_units"],
    },
    {
        "topic": "audience_targeting",
        "title": "About Ad Targeting in TikTok Ads Manager",
        "url": "https://ads.tiktok.com/help/article/ad-targeting?lang=en",
        "publisher": "TikTok for Business",
        "summary": "官方定向维度包括地域、年龄、性别、兴趣、行为、购买意图和设备，实际可用性随市场变化。",
        "supports": ["ad_unit.geo", "ad_unit.demographics", "ad_unit.audiences"],
    },
    {
        "topic": "location_targeting",
        "title": "How do I set up location targeting",
        "url": "https://support.google.com/google-ads/answer/10835274?hl=en",
        "publisher": "Google Ads Help",
        "summary": "官方说明地域可按国家、地区、城市或位置半径设置，过小的范围可能无法稳定投放。",
        "supports": ["ad_unit.geo"],
    },
    {
        "topic": "demographic_targeting",
        "title": "About demographic targeting",
        "url": "https://support.google.com/google-ads/answer/2580383?hl=en",
        "publisher": "Google Ads Help",
        "summary": "官方人口统计定向可包含年龄、性别等维度，具体选项取决于市场和广告类型。",
        "supports": ["ad_unit.demographics"],
    },
]


class _SearchParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results: list[dict] = []
        self._active: dict | None = None
        self._capture_link = False
        self._capture_snippet = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        class_name = values.get("class", "")
        if tag == "a" and "result__a" in class_name:
            self._active = {"title": "", "url": _unwrap_ddg(values.get("href", "")), "snippet": ""}
            self._capture_link = True
        elif "result__snippet" in class_name and self._active:
            self._capture_snippet = True

    def handle_endtag(self, tag):
        if tag == "a" and self._capture_link:
            self._capture_link = False
        if self._capture_snippet and tag in {"a", "div", "span"}:
            self._capture_snippet = False
            if self._active and self._active["url"]:
                self.results.append(self._active)
            self._active = None

    def handle_data(self, data):
        if self._active and self._capture_link:
            self._active["title"] += data.strip()
        elif self._active and self._capture_snippet:
            self._active["snippet"] += " " + data.strip()


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.text: list[str] = []
        self._title = False
        self._capture = False
        self._drop = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self._drop += 1
        elif not self._drop and tag == "title":
            self._title = True
        elif not self._drop and tag in {"p", "h1", "h2", "h3", "li"}:
            self._capture = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self._drop:
            self._drop -= 1
        elif tag == "title":
            self._title = False
        elif tag in {"p", "h1", "h2", "h3", "li"}:
            self._capture = False

    def handle_data(self, data):
        value = re.sub(r"\s+", " ", data).strip()
        if not value or self._drop:
            return
        if self._title:
            self.title += value
        elif self._capture and sum(map(len, self.text)) < 5000:
            self.text.append(value)


def _unwrap_ddg(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        return unquote(target)
    return url


async def _is_public_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    if parsed.hostname.lower() in {"localhost", "localhost.localdomain"}:
        return False
    try:
        addresses = await asyncio.to_thread(socket.getaddrinfo, parsed.hostname, parsed.port or 443)
    except OSError:
        return False
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address[4][0])
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def build_queries(request: CreateMediaPlanRequest) -> list[str]:
    product = request.product.name
    areas = " ".join(request.business.service_areas[:4])
    return [
        f"{product} 消费人群 购买场景 行业报告",
        f"{product} 家装 市场 趋势 {areas}",
        f"{product} 广告 投放 人群 兴趣",
        f"{product} 广告 合规 注意事项",
    ][: request.research.max_queries]


def curated_evidence() -> list[ResearchEvidence]:
    retrieved_at = datetime.now(timezone.utc).isoformat()
    return [ResearchEvidence(
        id=f"official-{index + 1:02d}",
        retrieved_at=retrieved_at,
        reliability="official",
        published_at="",
        **item,
    ) for index, item in enumerate(CURATED_EVIDENCE)]


async def _search(query: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False, headers={"User-Agent": "MujingResearch/0.1"}) as client:
        response = await client.get(SEARCH_URL, params={"q": query})
    if not response.is_success or len(response.content) > MAX_PAGE_BYTES:
        return []
    parser = _SearchParser()
    parser.feed(response.text)
    return parser.results[:5]


async def _read_result(result: dict, index: int) -> ResearchEvidence | None:
    url = result.get("url", "")
    if not await _is_public_url(url):
        return None
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False, headers={"User-Agent": "MujingResearch/0.1"}) as client:
            response = await client.get(url)
    except httpx.HTTPError:
        return None
    if not response.is_success or len(response.content) > MAX_PAGE_BYTES:
        return None
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        return None
    parser = _PageParser()
    parser.feed(response.text)
    summary = " ".join(parser.text)[:700] or result.get("snippet", "")[:700]
    if not summary:
        return None
    hostname = urlparse(url).hostname or "公开网页"
    return ResearchEvidence(
        id=f"web-{index:02d}",
        topic="product_market_research",
        title=(parser.title or result.get("title") or hostname)[:180],
        url=url[:1000],
        publisher=hostname[:120],
        published_at="",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        reliability="public_web",
        supports=["strategy_summary", "ad_unit.audiences"],
    )


async def research(request: CreateMediaPlanRequest) -> tuple[list[ResearchEvidence], list[str]]:
    evidence = curated_evidence()
    warnings: list[str] = []
    if not request.research.enabled:
        warnings.append("本次未启用公开网络检索，仅使用内置官方平台资料")
        return evidence, warnings
    results: list[dict] = []
    try:
        for query in build_queries(request):
            results.extend(await _search(query))
    except httpx.HTTPError:
        warnings.append("公开网络搜索暂时不可用，方案已使用官方资料和业务输入降级生成")
        return evidence, warnings
    unique: list[dict] = []
    seen = set()
    for result in results:
        url = result.get("url")
        if url and url not in seen:
            seen.add(url)
            unique.append(result)
        if len(unique) >= request.research.max_pages:
            break
    pages = await asyncio.gather(*(_read_result(result, index + 1) for index, result in enumerate(unique)))
    evidence.extend(page for page in pages if page)
    if not any(item.reliability == "public_web" for item in evidence):
        warnings.append("未读取到可用的公开行业页面，具体成本与城市优先级需要实投或历史数据验证")
    return evidence, warnings

