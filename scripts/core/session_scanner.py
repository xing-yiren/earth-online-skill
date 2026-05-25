"""Cross-session task scanner for Earth Online onboarding."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


_SESSIONS_ROOT = Path(os.environ.get("_EO_SESSION_SCAN_ROOT_OVERRIDE", Path.home() / ".claude" / "projects"))

# Task-indicating keywords that suggest a user message describes an ongoing or planned task.
_TASK_INDICATORS = [
    re.compile(r"(?:需要|必须|应该|得|要|打算|计划|准备|想|争取)\s*(?:去\s*)?(?:做|完成|整理|写|开发|实现|修复|处理|补|改|加|优化|重构|部署|发布|测试|配置|迁移|升级|清理|同步|导出|导入|阅读|学习|练习|复习|记录|总结|汇报|跟进|确认|验证|检查|调研|分析|设计|搭建|创建|调整|更新|替换|跟踪|维护|采集|抓取|爬|监控|备份|恢复|转化|翻译|校对|审查|合并|拆分|重构|排查|定位|解决|支持|协助|配合|对接|联调|上线|发布|回滚|扩容|缩容|压测|评测|对比|选型|评估|规划|制定|梳理|盘点|归档|分类|标记|标注|清洗|去重|格式化|规范化|标准化|自动化|脚本化|模块化|组件化|封装|抽象|解耦|集成|对接|适配|移植|重写)"),
    re.compile(r"(?:每天|每日|天天|日常|坚持|养成|习惯|定期|经常|时不时|每周|每月).*(?:做|完成|整理|写|阅读|运动|锻炼|冥想|跑步|学习|练习|复习|记录|总结|打卡|签到|更新|维护|检查|备份|清理)"),
    re.compile(r"^(?:TODO|TASK|FIXME|HACK|XXX|IDEA|NOTE):\s*(.+)", re.UNICODE | re.IGNORECASE),
]

# Patterns that indicate a message is NOT a task — one-off commands, replies, etc.
_TRIVIAL_PATTERNS = [
    re.compile(r"^(?:好的|可以|行|嗯|对|是的|没错|OK|ok|知道了|明白|懂了|没问题|不用|算了|没事|随便|都行)$"),
    re.compile(r"^(?:提交|推送|push|commit|合并|merge|拉取|pull|fetch|签出|checkout|变基|rebase|贮藏|stash)\s*(?:commit|代码|分支)?(?:\s*(?:吧|一下|了))?$"),
    re.compile(r"^(?:测试|试试|试一下|看看|查看|看一下|瞧瞧|搜索|找一下|查一下|帮我查|帮我找)\b.*$"),
    re.compile(r"^(?:继续|继续吧|继续开发|请继续|go on|继续下一步|next)\b.*$"),
    re.compile(r"^(?:谢谢|多谢|感谢|辛苦了|好的谢谢|OK谢谢|ok)"),
    re.compile(r"^[?？].*$"),
    re.compile(r"^(?:你好|hi|hello|嗨|在吗|在不|halo)"),
    re.compile(r"^(?:重启|重新|重来|重新开始|再来|再试|retry)"),
    re.compile(r"^/[\w-]+"),
    re.compile(r"^(?:刚才|刚刚|之前|上次|上回|昨天|今天|现在|当前|目前)\b(?!.*(?:需要|要做|计划|准备|安排|处理|搞定))"),
]

_MIN_CANDIDATE_LENGTH = 8
_MAX_CANDIDATE_LENGTH = 100

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
        for c in sorted(all_candidates, key=lambda c: c.get("score", 0), reverse=True):
            key = c["name"].strip().lower()
            if key not in seen:
                seen.add(key)
                # Remove internal scoring field from output
                c.pop("score", None)
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
        """Extract task candidates from a session file.

        Only considers the *first substantive user message* in each session
        (the one that started the conversation), plus any later messages that
        score highly as task descriptions.
        """
        candidates = []
        first_user_message = None
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

                    score = self._score_task(content)
                    if score > 0:
                        name = self._summarize_task(content)
                        candidates.append({
                            "name": name,
                            "score": score,
                            "source": "session_scan",
                            "source_detail": f"会话记录（{project_name}）",
                            "raw_text": content[:200],
                        })

                    if first_user_message is None:
                        first_user_message = content
        except Exception:
            pass

        # If no candidates found via scoring, try the first user message as fallback
        if not candidates and first_user_message:
            score = self._score_task(first_user_message)
            if score > 0 or (len(first_user_message) >= _MIN_CANDIDATE_LENGTH and not self._is_trivial(first_user_message)):
                name = self._summarize_task(first_user_message)
                candidates.append({
                    "name": name,
                    "score": max(score, 1),
                    "source": "session_scan",
                    "source_detail": f"会话记录（{project_name}）",
                    "raw_text": first_user_message[:200],
                })

        # Sort by score descending, take top 5 per session
        candidates.sort(key=lambda c: c["score"], reverse=True)
        return candidates[:5]

    def _clean_content(self, content: str) -> str:
        if "<local-command-caveat>" in content:
            return ""
        if any(content.strip().startswith(p) for p in _SKIP_PREFIXES):
            return ""

        content = re.sub(r"<[^>]+>", "", content)
        content = content.strip()
        return content

    def _is_trivial(self, text: str) -> bool:
        for pattern in _TRIVIAL_PATTERNS:
            if pattern.search(text):
                return True
        return False

    def _score_task(self, text: str) -> int:
        """Score a message from 0-10 for how likely it describes a real task."""
        if len(text) < _MIN_CANDIDATE_LENGTH or len(text) > _MAX_CANDIDATE_LENGTH:
            return 0
        if text.endswith("?") or text.endswith("？") or text.endswith("吗") or text.endswith("呢") or text.endswith("吧"):
            return 0
        if self._is_trivial(text):
            return 0

        score = 0

        # Contains a task indicator keyword pair
        for pattern in _TASK_INDICATORS:
            if pattern.search(text):
                score += 5
                break

        # Longer, more specific descriptions score higher
        if len(text) >= 20:
            score += 2
        if len(text) >= 40:
            score += 1

        # Contains a concrete deliverable (file, document, number, etc.)
        if re.search(r"(?:\.xlsx|\.csv|\.json|\.md|\.py|\.ts|\.js|\.html|\.css|\.sql|\.pdf|\.doc|\.pptx|\.txt|http[s]?://)", text):
            score += 2

        # Has temporal commitment
        if re.search(r"(?:每天|每日|天天|日常|坚持|养成|习惯|定期|经常|时不时|每周|每月|本周|这周|本月|今年)", text):
            score += 2

        return min(score, 10)

    def _summarize_task(self, text: str) -> str:
        """Create a concise task name from the raw message."""
        cleaned = text.strip()
        # Remove common conversational prefixes
        cleaned = re.sub(r"^(?:我需要|我要|我想|我打算|我计划|我准备|请|帮我|帮忙|麻烦|能不能|可以|可否|是否)\s*", "", cleaned)
        # Remove trailing punctuation
        cleaned = cleaned.rstrip("。，！？,.!?；;：: ")
        # Truncate if still too long
        if len(cleaned) > _MAX_CANDIDATE_LENGTH:
            cleaned = cleaned[:_MAX_CANDIDATE_LENGTH - 3] + "..."
        return cleaned
