import httpx
import asyncio
import logging
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(self):
        self.timeout = 30
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tiktok.com/',
        }

    def _build_proxy_url(self, proxy) -> Optional[str]:
        """构建代理URL字符串"""
        if not proxy:
            return None
        auth = f"{proxy.username}:{proxy.password}@" if proxy.username else ""
        return f"{proxy.proxy_type}://{auth}{proxy.host}:{proxy.port}"

    async def fetch_user_info(self, username: str, proxy=None) -> Dict[str, Any]:
        """
        抓取TikTok用户信息。
        返回格式: {success: bool, data: dict | None, error: str | None}
        """
        proxy_url = self._build_proxy_url(proxy)
        proxies = {"all://": proxy_url} if proxy_url else None

        try:
            async with httpx.AsyncClient(
                proxies=proxies,
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                # 尝试 TikTok web API (非官方)
                result = await self._try_web_api(client, username)
                if result['success']:
                    return result

                # 备用: TikTok oEmbed API（仅能获取基础信息）
                result = await self._try_oembed_api(client, username)
                if result['success']:
                    return result

                return {'success': False, 'data': None, 'error': 'All API endpoints failed'}

        except httpx.ProxyError as e:
            logger.error(f"Proxy error for {username}: {e}")
            return {'success': False, 'data': None, 'error': f'Proxy error: {str(e)[:200]}'}
        except httpx.TimeoutException as e:
            logger.error(f"Timeout for {username}: {e}")
            return {'success': False, 'data': None, 'error': f'Timeout: {str(e)[:200]}'}
        except Exception as e:
            logger.error(f"Scrape error for {username}: {e}")
            return {'success': False, 'data': None, 'error': str(e)[:200]}

    async def _try_web_api(self, client: httpx.AsyncClient, username: str) -> Dict[str, Any]:
        """尝试 TikTok 非官方 web API"""
        try:
            url = f"https://www.tiktok.com/api/user/detail/?uniqueId={username}&aid=1988&app_language=en&app_name=tiktok_web&device_platform=web_pc"
            response = await client.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                user_info = data.get('userInfo', {})
                user = user_info.get('user', {})
                stats = user_info.get('stats', {})

                if user.get('id'):
                    # 解析注册时间（Unix 时间戳）
                    create_time = user.get('createTime')
                    account_created_at = None
                    if create_time:
                        try:
                            account_created_at = datetime.utcfromtimestamp(int(create_time))
                        except (ValueError, OSError):
                            pass
                    return {
                        'success': True,
                        'data': {
                            'tiktok_id': user.get('id'),
                            'sec_uid': user.get('secUid'),
                            'nickname': user.get('nickname'),
                            'avatar_url': user.get('avatarMedium') or user.get('avatarLarger'),
                            'bio': user.get('signature'),
                            'follower_count': stats.get('followerCount', 0),
                            'following_count': stats.get('followingCount', 0),
                            'like_count': stats.get('heartCount', 0),
                            'video_count': stats.get('videoCount', 0),
                            'region': user.get('region'),
                            'account_created_at': account_created_at,
                        },
                        'error': None
                    }

            return {'success': False, 'data': None, 'error': f'Web API HTTP {response.status_code}'}

        except Exception as e:
            logger.debug(f"Web API failed for {username}: {e}")
            return {'success': False, 'data': None, 'error': str(e)[:200]}

    async def _try_oembed_api(self, client: httpx.AsyncClient, username: str) -> Dict[str, Any]:
        """尝试 TikTok oEmbed API（备用，数据有限）"""
        try:
            url = f"https://www.tiktok.com/@{username}"
            response = await client.get(url, headers=self.headers)

            if response.status_code == 200:
                # 尝试从页面中提取 __UNIVERSAL_DATA_FOR_REHYDRATION__
                content = response.text
                import json
                import re
                pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>'
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    try:
                        page_data = json.loads(match.group(1))
                        # 尝试从页面数据中提取用户信息
                        user_detail = (
                            page_data
                            .get('__DEFAULT_SCOPE__', {})
                            .get('webapp.user-detail', {})
                            .get('userInfo', {})
                        )
                        user = user_detail.get('user', {})
                        stats = user_detail.get('stats', {})
                        if user.get('id'):
                            create_time = user.get('createTime')
                            account_created_at = None
                            if create_time:
                                try:
                                    account_created_at = datetime.utcfromtimestamp(int(create_time))
                                except (ValueError, OSError):
                                    pass
                            return {
                                'success': True,
                                'data': {
                                    'tiktok_id': user.get('id'),
                                    'sec_uid': user.get('secUid'),
                                    'nickname': user.get('nickname'),
                                    'avatar_url': user.get('avatarMedium') or user.get('avatarLarger'),
                                    'bio': user.get('signature'),
                                    'follower_count': stats.get('followerCount', 0),
                                    'following_count': stats.get('followingCount', 0),
                                    'like_count': stats.get('heartCount', 0),
                                    'video_count': stats.get('videoCount', 0),
                                    'region': user.get('region'),
                                    'account_created_at': account_created_at,
                                },
                                'error': None
                            }
                    except (json.JSONDecodeError, KeyError):
                        pass

            return {'success': False, 'data': None, 'error': f'oEmbed HTTP {response.status_code}'}

        except Exception as e:
            logger.debug(f"oEmbed API failed for {username}: {e}")
            return {'success': False, 'data': None, 'error': str(e)[:200]}

    async def fetch_user_videos(self, sec_uid: str, proxy=None, max_count: int = 20) -> Dict[str, Any]:
        """
        使用TikTok移动端API抓取用户视频列表（已验证可用的方案）
        返回格式: {success: bool, data: list | None, error: str | None}
        
        Args:
            sec_uid: 用户的sec_uid
            proxy: 代理配置
            max_count: 最多获取的视频数量（默认20）
        """
        proxy_url = self._build_proxy_url(proxy)
        proxies = {"all://": proxy_url} if proxy_url else None

        try:
            # 生成设备参数
            device_id = str(random.randint(10**18, 10**19 - 1))
            iid = str(random.randint(7000000000000000000, 7999999999999999999))
            openudid = ''.join([format(random.randint(0, 255), '02x') for _ in range(16)])
            cdid = ''.join([format(random.randint(0, 255), '02x') for _ in range(16)])
            
            async with httpx.AsyncClient(
                proxies=proxies,
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                # 使用移动端API端点
                base_url = "https://api16-normal-c-alisg.tiktokv.com/lite/v2/public/item/list/"
                
                # 构建参数（模拟真实移动设备）
                params = {
                    'source': '0',
                    'sec_user_id': sec_uid,
                    'count': str(min(max_count, 20)),  # 单次最多20个
                    'max_cursor': '0',
                    'filter_private': '1',
                    'lite_flow_schedule': 'new',
                    'cdn_cache_is_login': '1',
                    'cdn_cache_strategy': 'v0',
                    'manifest_version_code': '370402',
                    '_rticket': str(int(time.time() * 1000)),
                    'app_language': 'en',
                    'app_type': 'normal',
                    'iid': iid,
                    'app_package': 'com.zhiliaoapp.musically.go',
                    'channel': 'googleplay',
                    'device_type': 'RMO-NX1',
                    'language': 'en',
                    'host_abi': 'arm64-v8a',
                    'locale': 'en',
                    'resolution': '1080*2316',
                    'openudid': openudid,
                    'update_version_code': '370402',
                    'ac2': '0',
                    'cdid': cdid,
                    'sys_region': 'US',
                    'os_api': '33',
                    'timezone_name': 'America/New_York',
                    'dpi': '480',
                    'carrier_region': 'US',
                    'ac': 'mobile',
                    'device_id': device_id,
                    'os_version': '13',
                    'timezone_offset': '-14400',
                    'version_code': '370402',
                    'app_name': 'musically_go',
                    'ab_version': '37.4.2',
                    'version_name': '37.4.2',
                    'device_brand': 'HONOR',
                    'op_region': 'US',
                    'ssmix': 'a',
                    'device_platform': 'android',
                    'build_number': '37.4.2',
                    'region': 'US',
                    'aid': '1340',
                    'ts': str(int(time.time())),
                }
                
                # 移动端 User-Agent
                headers = {
                    'User-Agent': 'com.zhiliaoapp.musically.go/370402 (Linux; Android 13; en; RMO-NX1; Build/HONORRMO-N21;tt-ok/3.12.13.27-ul)',
                    'Accept': '*/*',
                }
                
                response = await client.get(base_url, params=params, headers=headers)
                
                logger.info(f"Mobile API response status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # 移动端API返回的字段名
                        aweme_list = data.get('aweme_list', [])
                        
                        if not aweme_list:
                            logger.warning(f"No aweme_list in response, response keys: {data.keys()}")
                            return {'success': False, 'data': None, 'error': 'No aweme_list in API response'}
                        
                        videos = []
                        for item in aweme_list:
                            # 移动端API的数据结构
                            video_id = item.get('aweme_id') or item.get('id')
                            statistics = item.get('statistics', {})
                            video_info_data = item.get('video', {})
                            
                            # 获取封面URL
                            cover_url = None
                            if 'cover' in video_info_data and isinstance(video_info_data['cover'], dict):
                                url_list = video_info_data['cover'].get('url_list', [])
                                if url_list:
                                    cover_url = url_list[0]
                            
                            video_info = {
                                'video_id': video_id,
                                'title': item.get('desc', ''),
                                'cover_url': cover_url,
                                'play_count': statistics.get('play_count', 0),
                                'like_count': statistics.get('digg_count', 0),
                                'comment_count': statistics.get('comment_count', 0),
                                'share_count': statistics.get('share_count', 0),
                                'published_at': item.get('create_time'),
                            }
                            videos.append(video_info)
                        
                        logger.info(f"Successfully fetched {len(videos)} videos from mobile API")
                        return {'success': True, 'data': videos, 'error': None}
                        
                    except ValueError as json_error:
                        response_preview = response.text[:200] if response.text else "(empty)"
                        logger.error(f"JSON parse error: {json_error}, response preview: {response_preview}")
                        return {'success': False, 'data': None, 'error': f'Invalid JSON response: {str(json_error)[:100]}'}

                return {'success': False, 'data': None, 'error': f'HTTP {response.status_code}'}

        except Exception as e:
            logger.error(f"Fetch videos error for sec_uid={sec_uid}: {e}")
            return {'success': False, 'data': None, 'error': str(e)[:200]}

    async def test_proxy(self, proxy) -> Dict[str, Any]:
        """测试代理连通性，访问 TikTok 主站"""
        proxy_url = self._build_proxy_url(proxy)
        proxies = {"all://": proxy_url} if proxy_url else None
        start = time.time()
        try:
            async with httpx.AsyncClient(
                proxies=proxies,
                timeout=10,
                follow_redirects=True
            ) as client:
                resp = await client.get('https://www.tiktok.com', headers=self.headers)
                elapsed = time.time() - start
                return {
                    'success': resp.status_code < 500,
                    'response_time': round(elapsed, 3),
                    'error': None
                }
        except Exception as e:
            return {
                'success': False,
                'response_time': round(time.time() - start, 3),
                'error': str(e)[:100]
            }


scraper_service = ScraperService()
