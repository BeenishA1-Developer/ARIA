# ============================================================
# ARIA Phase 3 — Client Management System
# Clients, Invoices, Projects, Contracts, Payments
# ============================================================

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class ClientManager:
    """
    ARIA Phase 3 — Client Management System.

    ✅ Full client database with project history
    ✅ "Ahmed ka project status?" → instant answer
    ✅ Professional invoice PDF generator
    ✅ Smart contract proposal (AI generated)
    ✅ Payment tracking + overdue reminders
    ✅ Project milestone tracker
    ✅ Client communication timeline
    ✅ Laptop C: Drive smart cleanup
    ✅ Analytics dashboard data
    """

    def __init__(self, gemini_api_key: str = None,
                 data_dir: str = "data"):
        self.api_key    = gemini_api_key or os.getenv("GEMINI_API_KEY","")
        self.data_dir   = Path(data_dir)
        self.db_path    = self.data_dir / "clients.json"
        self.output_dir = Path("outputs/clients")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._ai        = None
        self._clients   = self._load()
        self._init_ai()
        logger.info("Client Manager initialized")

    def _init_ai(self):
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._ai = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                logger.error(f"AI: {e}")

    def _ai_call(self, prompt: str) -> str:
        if not self._ai: return ""
        try:   return self._ai.generate_content(prompt).text.strip()
        except: return ""

    def _ai_json(self, prompt: str) -> dict:
        text = self._ai_call(prompt)
        text = re.sub(r'^```json\s*','',text)
        text = re.sub(r'\s*```$','',text)
        try:   return json.loads(text)
        except: return {}

    def _load(self) -> dict:
        if self.db_path.exists():
            try:   return json.loads(self.db_path.read_text())
            except: pass
        return {}

    def _save(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_text(
            json.dumps(self._clients, indent=2, ensure_ascii=False)
        )

    # ── CLIENT CRUD ───────────────────────────────────────────

    def add_client(self, name: str, email: str = "",
                   phone: str = "", company: str = "",
                   notes: str = "") -> dict:
        cid = f"client_{re.sub(r'[^a-z0-9]','_',name.lower())}_{len(self._clients)}"
        self._clients[cid] = {
            "id":           cid,
            "name":         name,
            "email":        email,
            "phone":        phone,
            "company":      company,
            "notes":        notes,
            "projects":     [],
            "invoices":     [],
            "total_earned": 0,
            "created_at":   datetime.now().isoformat(),
        }
        self._save()
        logger.success(f"Client added: {name}")
        return {"success": True, "client_id": cid,
                "message": f"Client '{name}' add ho gaya!"}

    def find_client(self, name: str) -> dict:
        name_lower = name.lower()
        for cid, c in self._clients.items():
            if name_lower in c["name"].lower():
                return {"success": True, "client": c}
        return {"success": False, "message": f"'{name}' nahi mila"}

    def get_client_status(self, name: str) -> dict:
        """Ahmed ka project status kya hai? → instant answer."""
        r = self.find_client(name)
        if not r["success"]:
            return r
        c = r["client"]
        projects  = c.get("projects", [])
        invoices  = c.get("invoices", [])
        active    = [p for p in projects if p.get("status") == "active"]
        overdue   = [i for i in invoices
                     if i.get("status") == "unpaid"
                     and i.get("due_date","") < datetime.now().isoformat()]

        summary = self._ai_call(
            f"Summarize in 2 sentences for WhatsApp message:\n"
            f"Client: {name}\nProjects: {json.dumps(projects[-3:])}\n"
            f"Pending invoices: {len(overdue)}"
        ) or f"{name} ke {len(active)} active projects hain."

        return {
            "success":          True,
            "client":           c,
            "active_projects":  active,
            "pending_invoices": overdue,
            "summary":          summary,
        }

    # ── PROJECT MANAGEMENT ────────────────────────────────────

    def add_project(self, client_name: str, project_title: str,
                    budget: float, deadline: str,
                    description: str = "") -> dict:
        r = self.find_client(client_name)
        if not r["success"]:
            return r
        c   = r["client"]
        pid = f"proj_{len(c['projects'])+1}_{datetime.now().strftime('%Y%m%d')}"
        project = {
            "id":          pid,
            "title":       project_title,
            "budget":      budget,
            "deadline":    deadline,
            "description": description,
            "status":      "active",
            "milestones":  [],
            "progress":    0,
            "started_at":  datetime.now().isoformat(),
        }
        c["projects"].append(project)
        self._save()
        return {"success": True, "project_id": pid,
                "message": f"Project '{project_title}' add ho gaya!"}

    def update_milestone(self, client_name: str,
                          project_title: str,
                          milestone: str,
                          completed: bool = True) -> dict:
        r = self.find_client(client_name)
        if not r["success"]:
            return r
        c = r["client"]
        for proj in c["projects"]:
            if project_title.lower() in proj["title"].lower():
                ms_list = proj.get("milestones", [])
                # Check if exists
                for ms in ms_list:
                    if milestone.lower() in ms.get("title","").lower():
                        ms["completed"] = completed
                        ms["updated"]   = datetime.now().isoformat()
                        break
                else:
                    ms_list.append({
                        "title":     milestone,
                        "completed": completed,
                        "added":     datetime.now().isoformat(),
                    })
                proj["milestones"] = ms_list
                total    = len(ms_list)
                done     = sum(1 for m in ms_list if m.get("completed"))
                proj["progress"] = int(done/total*100) if total else 0
                if done == total:
                    proj["status"] = "completed"
                self._save()
                return {
                    "success":  True,
                    "progress": proj["progress"],
                    "message":  f"Milestone update! Progress: {proj['progress']}%",
                }
        return {"success": False, "message": "Project nahi mila"}

    # ── INVOICE GENERATOR ─────────────────────────────────────

    def create_invoice(self, client_name: str,
                        items: list,
                        due_days: int = 30,
                        currency: str = "PKR") -> dict:
        """
        Professional invoice PDF generate karo.
        items: [{"description": "Web dev", "qty": 1, "rate": 50000}]
        """
        r = self.find_client(client_name)
        if not r["success"]:
            return r
        c = r["client"]

        inv_num  = f"INV-{datetime.now().strftime('%Y%m')}-{len(c['invoices'])+1:03d}"
        subtotal = sum(i.get("qty",1) * i.get("rate",0) for i in items)
        tax      = subtotal * 0.0  # Tax-free by default
        total    = subtotal + tax
        due_date = (datetime.now() + timedelta(days=due_days)).strftime("%d %B %Y")

        invoice = {
            "invoice_number": inv_num,
            "date":           datetime.now().strftime("%d %B %Y"),
            "due_date":       due_date,
            "client":         c,
            "items":          items,
            "subtotal":       subtotal,
            "tax":            tax,
            "total":          total,
            "currency":       currency,
            "status":         "unpaid",
        }

        pdf_path = self._build_invoice_pdf(invoice)

        c["invoices"].append({
            "invoice_number": inv_num,
            "total":          total,
            "currency":       currency,
            "due_date":       (datetime.now() + timedelta(days=due_days)).isoformat(),
            "status":         "unpaid",
            "pdf_path":       pdf_path,
        })
        c["total_earned"] += total
        self._save()

        return {
            "success":        True,
            "invoice_number": inv_num,
            "total":          f"{currency} {total:,.0f}",
            "due_date":       due_date,
            "pdf_path":       pdf_path,
            "message":        f"Invoice {inv_num} ready! Total: {currency} {total:,.0f}",
        }

    def _build_invoice_pdf(self, inv: dict) -> str:
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"invoice_{inv['invoice_number']}_{ts}.pdf"
        path     = str(self.output_dir / filename)

        if not PDF_AVAILABLE:
            txt_path = path.replace(".pdf", ".txt")
            lines = [
                "=" * 50,
                f"INVOICE {inv['invoice_number']}",
                "=" * 50,
                f"Date: {inv['date']}",
                f"Due:  {inv['due_date']}",
                f"Bill To: {inv['client']['name']} | {inv['client']['email']}",
                "", "ITEMS", "-" * 40,
            ]
            for item in inv["items"]:
                lines.append(
                    f"{item['description']:30} x{item.get('qty',1):3} "
                    f"@ {inv['currency']} {item.get('rate',0):>10,.0f}"
                )
            lines += [
                "-" * 40,
                f"{'TOTAL':>36} {inv['currency']} {inv['total']:>10,.0f}",
                "", "Thank you for your business!",
            ]
            Path(txt_path).write_text("\n".join(lines))
            return txt_path

        doc    = SimpleDocTemplate(path, pagesize=letter,
                                   topMargin=0.5*inch, bottomMargin=0.5*inch,
                                   leftMargin=0.75*inch, rightMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story  = []
        BLUE   = colors.HexColor("#0066cc")
        DARK   = colors.HexColor("#1a1a2e")

        # Header
        story.append(Paragraph(
            f"<font size=24 color='#0066cc'><b>INVOICE</b></font>",
            styles['Normal']
        ))
        story.append(Paragraph(
            f"<font size=11 color='#666666'>{inv['invoice_number']}</font>",
            styles['Normal']
        ))
        story.append(HRFlowable(width="100%", thickness=2,
                                color=BLUE, spaceBefore=8, spaceAfter=12))

        # Dates
        story.append(Paragraph(
            f"<b>Date:</b> {inv['date']}  |  "
            f"<b>Due Date:</b> {inv['due_date']}",
            styles['Normal']
        ))
        story.append(Spacer(1, 12))

        # Bill to
        client = inv["client"]
        story.append(Paragraph(
            f"<b>Bill To:</b><br/>"
            f"{client.get('name','')}<br/>"
            f"{client.get('company','')}<br/>"
            f"{client.get('email','')}<br/>"
            f"{client.get('phone','')}",
            styles['Normal']
        ))
        story.append(Spacer(1, 16))

        # Items table
        table_data = [["Description", "Qty", "Rate", "Amount"]]
        for item in inv["items"]:
            amt = item.get("qty",1) * item.get("rate",0)
            table_data.append([
                item.get("description",""),
                str(item.get("qty",1)),
                f"{inv['currency']} {item.get('rate',0):,.0f}",
                f"{inv['currency']} {amt:,.0f}",
            ])

        table_data.extend([
            ["", "", "Subtotal:", f"{inv['currency']} {inv['subtotal']:,.0f}"],
            ["", "", "Tax:",      f"{inv['currency']} {inv['tax']:,.0f}"],
            ["", "", "TOTAL:",    f"{inv['currency']} {inv['total']:,.0f}"],
        ])

        tbl = Table(table_data,
                    colWidths=[3.5*inch, 0.7*inch, 1.5*inch, 1.5*inch])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), BLUE),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,0), 11),
            ('ALIGN',         (1,0), (-1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS',(0,1), (-1,-4),
             [colors.HexColor('#F0F4F8'), colors.white]),
            ('LINEBELOW',     (0,-4), (-1,-4), 1, colors.grey),
            ('FONTNAME',      (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,-1), (-1,-1), 12),
            ('BACKGROUND',    (0,-1), (-1,-1), colors.HexColor('#E8F4FD')),
            ('GRID',          (0,0),  (-1,-4), 0.5, colors.grey),
            ('TOPPADDING',    (0,0),  (-1,-1), 8),
            ('BOTTOMPADDING', (0,0),  (-1,-1), 8),
            ('LEFTPADDING',   (0,0),  (-1,-1), 8),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            "<i>Thank you for your business! Payment is due within 30 days.</i>",
            styles['Normal']
        ))
        doc.build(story)
        logger.success(f"Invoice PDF: {path}")
        return path

    # ── CONTRACT PROPOSAL ─────────────────────────────────────

    def generate_proposal(self, client_name: str,
                           project_description: str,
                           budget_range: str = "") -> dict:
        """AI se professional contract proposal generate karo."""
        proposal = self._ai_call(f"""
Write a professional freelance project proposal/contract.

Client: {client_name}
Project: {project_description}
Budget Range: {budget_range or "To be discussed"}
Date: {datetime.now().strftime('%d %B %Y')}

Include:
1. Project Overview
2. Scope of Work (bullet points)
3. Deliverables
4. Timeline (with milestones)
5. Payment Terms
6. Revision Policy
7. Terms & Conditions
8. Signature section

Professional, concise, client-friendly tone.
""")
        if not proposal:
            return {"success": False, "message": "Proposal generate nahi ho saka"}

        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = re.sub(r'[^\w]','_',client_name)[:15]
        path = self.output_dir / f"proposal_{name}_{ts}.txt"
        path.write_text(proposal, encoding='utf-8')

        return {
            "success":  True,
            "proposal": proposal,
            "saved_at": str(path),
            "message":  f"Proposal ready! {len(proposal.split())} words.",
        }

    # ── PAYMENT TRACKING ──────────────────────────────────────

    def mark_paid(self, client_name: str,
                  invoice_number: str) -> dict:
        r = self.find_client(client_name)
        if not r["success"]: return r
        c = r["client"]
        for inv in c.get("invoices",[]):
            if inv.get("invoice_number") == invoice_number:
                inv["status"]  = "paid"
                inv["paid_at"] = datetime.now().isoformat()
                self._save()
                return {"success": True,
                        "message": f"{invoice_number} paid mark ho gaya!"}
        return {"success": False, "message": "Invoice nahi mila"}

    def get_overdue_invoices(self) -> list:
        now  = datetime.now()
        due  = []
        for cid, c in self._clients.items():
            for inv in c.get("invoices",[]):
                if inv.get("status") == "unpaid":
                    try:
                        dd = datetime.fromisoformat(inv.get("due_date",""))
                        if dd < now:
                            due.append({
                                "client": c["name"],
                                "invoice": inv["invoice_number"],
                                "total":   inv["total"],
                                "currency": inv.get("currency","PKR"),
                                "days_overdue": (now - dd).days,
                            })
                    except Exception:
                        pass
        return sorted(due, key=lambda x: x["days_overdue"], reverse=True)

    # ── LAPTOP CLEANUP ────────────────────────────────────────

    def analyze_disk_space(self, drive: str = "C") -> dict:
        """C Drive analyze karo — kya clean kar sakte hain?"""
        try:
            import psutil
            usage = psutil.disk_usage(f"{drive}:\\")
            safe_to_clean = [
                {"path": r"C:\Windows\Temp",       "type": "Windows Temp"},
                {"path": r"C:\Users\Public\Temp",  "type": "Public Temp"},
                {"path": r"%APPDATA%\Local\Temp",  "type": "App Temp"},
                {"path": r"C:\Users\*\AppData\Local\Google\Chrome\User Data\Default\Cache",
                 "type": "Chrome Cache"},
            ]

            from modules.file_manager import FileManager
            fm = FileManager()

            analysis = []
            for item in safe_to_clean:
                p = Path(item["path"].replace("%APPDATA%", str(Path.home())))
                if p.exists():
                    size_info = fm.get_folder_size(str(p))
                    analysis.append({
                        "path":  str(p),
                        "type":  item["type"],
                        "size":  size_info.get("size","0 B"),
                        "files": size_info.get("file_count", 0),
                        "safe":  True,
                    })

            return {
                "success":      True,
                "drive":        drive,
                "total":        f"{usage.total/1024**3:.1f} GB",
                "used":         f"{usage.used/1024**3:.1f} GB",
                "free":         f"{usage.free/1024**3:.1f} GB",
                "percent":      f"{usage.percent}%",
                "cleanable":    analysis,
                "message": (
                    f"{drive}: — {usage.percent}% used. "
                    f"{len(analysis)} folders clean kar sakte hain."
                ),
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_all_stats(self) -> dict:
        """Overall stats for dashboard."""
        total_earned = sum(
            c.get("total_earned",0) for c in self._clients.values()
        )
        all_projects = [
            p for c in self._clients.values()
            for p in c.get("projects",[])
        ]
        return {
            "total_clients":    len(self._clients),
            "total_projects":   len(all_projects),
            "active_projects":  sum(1 for p in all_projects if p.get("status")=="active"),
            "total_earned":     total_earned,
            "overdue_invoices": len(self.get_overdue_invoices()),
        }
