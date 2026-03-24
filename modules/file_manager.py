# ============================================================
# ARIA - File Manager Module
# Files dhoondna, organize, PDF merge, folder create
# ============================================================

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from loguru import logger

try:
    from PyPDF2 import PdfMerger
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class FileManager:
    """
    ARIA ka File Manager.
    - Files search karna — poore laptop mein
    - Folders organize karna — type ke hisaab se
    - PDF merge karna
    - Duplicate files dhoondna
    - Folders create karna
    """

    # File type categories
    FILE_CATEGORIES = {
        "Images":     [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"],
        "Videos":     [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
        "Documents":  [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf"],
        "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
        "Presentations": [".ppt", ".pptx", ".odp"],
        "Audio":      [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
        "Archives":   [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "Code":       [".py", ".js", ".ts", ".html", ".css", ".json", ".xml",
                       ".java", ".cpp", ".c", ".cs", ".php", ".sql"],
        "Executables": [".exe", ".msi", ".bat", ".cmd", ".sh"],
    }

    def __init__(self, search_paths: List[Path] = None):
        self.search_paths = search_paths or [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Pictures",
            Path.home() / "Videos",
            Path.home() / "Music",
        ]
        logger.info("File Manager initialized")

    # ── FILE SEARCH ───────────────────────────────────────────

    def search_files(self, query: str, file_type: str = None,
                     max_results: int = 20) -> List[dict]:
        """
        Files search karo — name ya extension se.
        query: file name ya keyword
        file_type: 'pdf', 'image', 'video', etc. (optional)
        """
        results = []
        query_lower = query.lower()

        # Determine extensions to search
        target_extensions = set()
        if file_type:
            ft_lower = file_type.lower()
            for category, exts in self.FILE_CATEGORIES.items():
                if ft_lower in category.lower() or ft_lower in [e.lstrip('.') for e in exts]:
                    target_extensions.update(exts)

        for search_path in self.search_paths:
            if not search_path.exists():
                continue
            try:
                for file_path in search_path.rglob("*"):
                    if not file_path.is_file():
                        continue

                    # Extension filter
                    if target_extensions:
                        if file_path.suffix.lower() not in target_extensions:
                            continue

                    # Name match
                    if query_lower and query_lower not in file_path.name.lower():
                        continue

                    stat = file_path.stat()
                    results.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": self._format_size(stat.st_size),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "extension": file_path.suffix.lower(),
                        "category": self._get_category(file_path.suffix),
                    })

                    if len(results) >= max_results:
                        break

            except PermissionError:
                logger.warning(f"Permission denied: {search_path}")
                continue

        # Sort by modified date (newest first)
        results.sort(key=lambda x: x["modified"], reverse=True)
        logger.info(f"File search '{query}': {len(results)} results")
        return results

    def find_file_by_name(self, filename: str) -> Optional[str]:
        """Exact file name se dhundho."""
        results = self.search_files(filename)
        if results:
            return results[0]["path"]
        return None

    # ── FOLDER ORGANIZE ───────────────────────────────────────

    def organize_folder(self, folder_path: str = None,
                        dry_run: bool = False) -> dict:
        """
        Folder organize karo — type ke hisaab se.
        dry_run=True: Sirf batao kya hoga, karo mat
        """
        if folder_path:
            target = Path(folder_path)
        else:
            target = Path.home() / "Downloads"

        if not target.exists():
            return {"error": f"Folder nahi mila: {folder_path}"}

        moves = []
        errors = []

        for file_path in target.iterdir():
            if not file_path.is_file():
                continue

            # Hidden files skip karo
            if file_path.name.startswith('.'):
                continue

            category = self._get_category(file_path.suffix)
            dest_folder = target / category
            dest_file = dest_folder / file_path.name

            # Duplicate name handle karo
            if dest_file.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                counter = 1
                while dest_file.exists():
                    dest_file = dest_folder / f"{stem}_{counter}{suffix}"
                    counter += 1

            moves.append({
                "file": file_path.name,
                "from": str(file_path),
                "to": str(dest_file),
                "category": category,
            })

        if not dry_run:
            for move in moves:
                try:
                    dest = Path(move["to"])
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(move["from"], move["to"])
                except Exception as e:
                    errors.append({"file": move["file"], "error": str(e)})
                    logger.error(f"Move failed: {move['file']} — {e}")

        result = {
            "folder": str(target),
            "files_organized": len(moves),
            "moves": moves,
            "errors": errors,
            "dry_run": dry_run,
        }
        logger.info(f"Folder organized: {len(moves)} files in {target}")
        return result

    # ── DUPLICATE FINDER ──────────────────────────────────────

    def find_duplicates(self, folder_path: str = None) -> List[dict]:
        """
        Duplicate files dhoondo — same name wale.
        """
        if folder_path:
            target = Path(folder_path)
        else:
            target = Path.home() / "Downloads"

        seen = {}
        duplicates = []

        for file_path in target.rglob("*"):
            if not file_path.is_file():
                continue

            key = (file_path.name, file_path.stat().st_size)
            if key in seen:
                duplicates.append({
                    "name": file_path.name,
                    "original": seen[key],
                    "duplicate": str(file_path),
                    "size": self._format_size(file_path.stat().st_size),
                })
            else:
                seen[key] = str(file_path)

        logger.info(f"Duplicates found: {len(duplicates)}")
        return duplicates

    # ── PDF MERGE ─────────────────────────────────────────────

    def merge_pdfs(self, pdf_paths: List[str], output_path: str = None) -> str:
        """
        Multiple PDFs ko merge karo.
        Returns: Output file path
        """
        if not PDF_AVAILABLE:
            return "Error: PyPDF2 install nahi hai — 'pip install PyPDF2'"

        if not output_path:
            output_path = str(Path.home() / "Desktop" / f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        merger = PdfMerger()
        merged_count = 0

        for pdf_path in pdf_paths:
            path = Path(pdf_path)
            if path.exists() and path.suffix.lower() == '.pdf':
                merger.append(str(path))
                merged_count += 1
                logger.info(f"PDF added: {path.name}")
            else:
                logger.warning(f"PDF nahi mila: {pdf_path}")

        if merged_count == 0:
            return "Error: Koi valid PDF nahi mila"

        merger.write(output_path)
        merger.close()
        logger.success(f"PDFs merged: {output_path}")
        return output_path

    # ── FOLDER CREATE ─────────────────────────────────────────

    def create_folder(self, folder_name: str, location: str = None) -> str:
        """Naya folder banao."""
        if location:
            parent = Path(location)
        else:
            parent = Path.home() / "Desktop"

        new_folder = parent / folder_name
        new_folder.mkdir(parents=True, exist_ok=True)
        logger.success(f"Folder created: {new_folder}")
        return str(new_folder)

    # ── DISK USAGE ────────────────────────────────────────────

    def get_folder_size(self, folder_path: str = None) -> dict:
        """Folder ki size batao."""
        if not folder_path:
            folder_path = str(Path.home())

        target = Path(folder_path)
        total_size = 0
        file_count = 0

        try:
            for f in target.rglob("*"):
                if f.is_file():
                    try:
                        total_size += f.stat().st_size
                        file_count += 1
                    except Exception:
                        pass
        except PermissionError:
            pass

        return {
            "folder": str(target),
            "size": self._format_size(total_size),
            "size_bytes": total_size,
            "file_count": file_count,
        }

    # ── HELPERS ───────────────────────────────────────────────

    def _get_category(self, extension: str) -> str:
        """File extension se category batao."""
        ext_lower = extension.lower()
        for category, extensions in self.FILE_CATEGORIES.items():
            if ext_lower in extensions:
                return category
        return "Others"

    def _format_size(self, size_bytes: int) -> str:
        """Bytes ko readable format mein."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes/1024**2:.1f} MB"
        else:
            return f"{size_bytes/1024**3:.2f} GB"
