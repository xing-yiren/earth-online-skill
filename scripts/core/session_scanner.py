"""Cross-session task scanner for Earth Online onboarding."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


_SESSIONS_ROOT = Path(os.environ.get("_EO_SESSION_SCAN_ROOT_OVERRIDE", Path.home() / ".claude" / "projects"))

_TASK_PATTERNS = [
    re.compile(r"(?:需要|要|打算|计划|准备|想|得|该|必须|应该)\s*(?:去\s*)?(?:做|完成|整理|写|开发|实现|修复|处理|弄|搞|补|改|加|删|优化|重构|部署|发布|测试|调试|配置|安装|迁移|升级|回滚|备份|清理|同步|导出|导入|提交|推送|合并|审查|阅读|学习|练习|复习|记录|总结|汇报|沟通|协调|安排|跟进|确认|验证|检查|调研|分析|设计|画|搭建|创建|新建|删除|取消|调整|修改|更新|替换|重命名|移动|复制|转换|格式化|压缩|解压|加密|解密|签名|验签|打包|上传|下载|发送|接收|转发|回复|评论|点赞|收藏|分享|订阅|取消订阅|注册|登录|注销|激活|禁用|启用|暂停|恢复|重启|关闭|开启|切换|选择|过滤|排序|搜索|查找|定位|导航|跳转|刷新|重试|回滚|撤销|恢复)(?:\S+)", re.UNICODE),
    re.compile(r"(?:每天|每日|天天|日常|坚持|养成|习惯|定期|经常|时不时).*(?:做|完成|整理|写|阅读|运动|锻炼|冥想|跑步|学习|练习|复习|记录|总结|打卡|签到)", re.UNICODE),
    re.compile(r"^(?:TODO|TASK|FIXME|HACK|XXX|IDEA|NOTE):\s*(.+)", re.UNICODE | re.IGNORECASE),
    re.compile(r"(?:主线|支线|任务|习惯|目标|计划|待办).*[:：]\s*(.+)", re.UNICODE),
]

_MIN_CANDIDATE_LENGTH = 4
_MAX_CANDIDATE_LENGTH = 80

_SKIP_PREFIXES = {
    "/clear", "/help", "/cost", "/status", "/config",
    "/tasks", "/todo", "/memory", "/add-dir", "/ide",
    "/model", "/style", "/theme", "/doctor", "/pr-comments",
    "/review-pr", "/rename",
}


class SessionScanner:
    def scan(self, payload: dict) -> dict:
        if not payload.get("confirmed_by_user"):
            return {
                "success": False,
                "error": "confirmation_required",
                "message": (
                    "跨会话扫描需要读取你所有项目的 Claude Code 会话记录，"
                    "包括对话内容和项目路径。\n"
                    "是否允许我扫描？请回复'确认'或'取消'。"
                ),
            }

        limit = payload.get("limit")
        projects_filter = payload.get("projects")

        if not _SESSIONS_ROOT.exists():
            return {"success": True, "candidates": [], "count": 0, "scanned_sessions": 0, "scanned_projects": 0}

        project_dirs = sorted(_SESSIONS_ROOT.iterdir())
        if projects_filter:
            project_dirs = [d for d in project_dirs if d.name in projects_filter]

        all_candidates = []
        scanned_sessions = 0

        for project_dir in project_dirs:
            if not project_dir.is_dir():
                continue
            candidates, session_count = self._scan_project(project_dir, limit)
            all_candidates.extend(candidates)
            scanned_sessions += session_count

        seen = set()
        unique = []
        for c in all_candidates:
            key = c["name"].strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return {
            "success": True,
            "candidates": unique,
            "count": len(unique),
            "scanned_sessions": scanned_sessions,
            "scanned_projects": len(project_dirs),
        }

    def _scan_project(self, project_dir: Path, limit: int | None) -> tuple[list[dict], int]:
        candidates = []
        session_count = 0

        for entry in sorted(project_dir.iterdir()):
            if not entry.is_file() or entry.suffix != ".jsonl":
                continue
            session_count += 1
            try:
                session_candidates = self._extract_from_session(entry, project_dir.name)
                candidates.extend(session_candidates)
            except Exception:
                continue

            if limit and len(candidates) >= limit:
                break

        return candidates, session_count

    def _extract_from_session(self, session_path: Path, project_name: str) -> list[dict]:
        candidates = []
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if record.get("type") != "user":
                        continue
                    if record.get("isMeta"):
                        continue

                    message = record.get("message", {})
                    content = message.get("content", "") if isinstance(message, dict) else ""
                    if not content or not isinstance(content, str):
                        continue

                    content = self._clean_content(content)
                    if not content:
                        continue

                    extracted = self._extract_task(content)
                    if extracted:
                        candidates.append({
                            "name": extracted,
                            "source": "session_scan",
                            "source_detail": f"会话记录（{project_name}）",
                            "raw_text": content[:200],
                        })
        except Exception:
            pass

        return candidates

    def _clean_content(self, content: str) -> str:
        if "<local-command-caveat>" in content:
            return ""
        if any(content.strip().startswith(p) for p in _SKIP_PREFIXES):
            return ""

        content = re.sub(r"<[^>]+>", "", content)
        content = content.strip()
        return content

    def _extract_task(self, text: str) -> str | None:
        if len(text) < _MIN_CANDIDATE_LENGTH or len(text) > _MAX_CANDIDATE_LENGTH:
            return None
        if text.endswith("?") or text.endswith("?") or text.endswith("吗") or text.endswith("呢") or text.endswith("吧"):
            return None

        for pattern in _TASK_PATTERNS:
            match = pattern.search(text)
            if match:
                if match.lastindex and match.lastindex >= 1:
                    result = match.group(1)
                else:
                    result = match.group(0)
                if result and _MIN_CANDIDATE_LENGTH <= len(result) <= _MAX_CANDIDATE_LENGTH:
                    return result.strip()
                return text.strip()

        return None
