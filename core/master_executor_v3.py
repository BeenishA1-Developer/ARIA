# ============================================================
# ARIA v3 — Master Executor FINAL (Phase 1 + 2 + 3 COMPLETE)
# ============================================================

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from loguru import logger
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text

sys.path.insert(0, str(Path(__file__).parent.parent))

# Phase 1 + 2
from core.master_executor_v2 import ARIAv2

# Phase 3
from modules.phase3.cv_manager          import CVManager
from modules.phase3.job_hunter          import JobHunter
from modules.phase3.social_media_manager import SocialMediaManager
from modules.phase3.website_manager     import WebsiteManager
from modules.phase3.client_manager      import ClientManager
from modules.phase3.nlp_phase3_patch    import patch_phase3_intents
from modules.phase3.opportunity_finder  import OpportunityFinder

from config.settings import GEMINI_API_KEY, DB_PATH, CHROMA_PATH, DATA_DIR

console = Console()


class ARIAv3(ARIAv2):
    """
    ARIA v3 FINAL — Phase 1 + Phase 2 + Phase 3 COMPLETE.
    Inherits all Phase 1+2 features, adds Phase 3.
    """

    VERSION = "3.0 FINAL"

    def __init__(self):
        # Init Phase 1+2
        super().__init__()

        console.print("[cyan]Loading Phase 3 modules...[/cyan]")

        # Phase 3 modules
        self.cv        = CVManager(gemini_api_key=GEMINI_API_KEY)
        self.jobs      = JobHunter(
            gemini_api_key=GEMINI_API_KEY,
            cv_manager=self.cv,
            email_system=self.gmail,
        )
        self.social    = SocialMediaManager(gemini_api_key=GEMINI_API_KEY)
        self.website   = WebsiteManager(gemini_api_key=GEMINI_API_KEY)
        self.clients   = ClientManager(gemini_api_key=GEMINI_API_KEY)
        self.opt       = OpportunityFinder(gemini_api_key=GEMINI_API_KEY, data_dir=str(DATA_DIR))

        # Conversational AI fallback
        self._chat_ai = None
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self._chat_ai = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                logger.error(f"Chat AI INIT error: {e}")

        # Add Phase 3 NLP intents
        patch_phase3_intents(self.nlp)

        logger.success("ARIA v3 — Phase 1+2+3 ALL READY ✅")

    # ═══════════════════════════════════════════════════════════
    # OVERRIDE ROUTE — add Phase 3
    # ═══════════════════════════════════════════════════════════

    def _route(self, intent: str, entities: dict, raw: str) -> str:

        # ── Phase 3 intents ───────────────────────────────────
        p3_map = {
            # CV
            "cv_build":       self._cv_build,
            "cv_improve":     self._cv_improve,
            "cv_customize":   self._cv_customize,
            "cv_ats_check":   self._cv_ats,
            "cover_letter":   self._cover_letter,
            "cv_versions":    self._cv_versions,
            # Jobs
            "job_search":     self._job_search,
            "job_apply":      self._job_apply,
            "job_followup":   self._job_followup,
            "job_status":     self._job_status,
            # Govt Opportunities ⭐
            "govt_opportunities": (
                # Smart routing: if 'apply' in raw → go to govt_apply
                self._govt_apply if any(w in raw.lower() for w in
                    ["apply","application","submit","karo"]) 
                    and any(w in raw.lower() for w in ["cv","resume","according"])
                else self._govt_opportunities
            ),
            "govt_apply":         self._govt_apply,
            # Social Media
            "content_create":   self._content_create,
            "hashtags_generate":self._hashtags,
            "trending_topics":  self._trending,
            "content_calendar": self._content_calendar,
            "caption_write":    self._caption,
            "viral_score":      self._viral_score,
            "social_report":    self._social_report,
            "competitor_social":self._competitor_social,
            # Website
            "blog_write":       self._blog_write,
            "service_page":     self._service_page,
            "seo_check":        self._seo_check,
            "git_push":         self._git_push,
            "website_generate": self._website_generate,
            # Client
            "client_add":       self._client_add,
            "client_status":    self._client_status,
            "invoice_create":   self._invoice_create,
            "proposal_generate":self._proposal,
            "payment_track":    self._payment_track,
            "disk_cleanup":     self._disk_cleanup,
        }

        if intent in p3_map:
            return p3_map[intent](entities, raw)

        # Fallback to Conversational AI if intent is completely unknown
        if intent == "unknown":
            return self._conversational_fallback(raw)

        # Fallback to Phase 1+2
        return super()._route(intent, entities, raw)

    def _conversational_fallback(self, raw: str) -> str:
        """Fallback to conversational AI using Gemini to act like a smart human assistant."""
        if not self._chat_ai:
            self.voice.speak("Samajh nahi aaya, aur AI key bhi available nahi hai.")
            return "unknown"
            
        system_prompt = (
            "You are ARIA, an Automated Responsive Intelligent Assistant.\n"
            "You are a highly capable, smart, and human-like personal assistant and developer companion.\n"
            "Respond to the user naturally, in the language they used (Urdu, Roman Urdu, or English).\n"
            "Keep responses VERY short, friendly, and conversational (max 1-2 sentences), suitable for Speech-To-Text.\n"
            "Do not use markdown like *asterisks*, as it will be spoken out loud.\n"
            "User's query: "
        )
        
        try:
            resp = self._chat_ai.generate_content(system_prompt + raw)
            text = resp.text.strip()
            # Clean up any potential markdown formatting
            text = re.sub(r'[*_#`]', '', text)
            self.voice.speak(text)
            return "chat_response"
        except Exception as e:
            logger.error(f"Chat execution failed: {e}")
            self.voice.speak("Network connection ka issue hai shayad, try again.")
            return "unknown"

    # ═══════════════════════════════════════════════════════════
    # CV MANAGER ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _cv_build(self, entities, raw) -> str:
        self.voice.speak("CV ki information dijiye — main banata hun...")
        console.print("[cyan]CV Information enter karein:[/cyan]")
        info = {}
        fields = [
            ("name",     "Poora naam"),
            ("email",    "Email"),
            ("phone",    "Phone number"),
            ("location", "Shehar, Mulk"),
            ("summary",  "Apne baare mein ek line (ya Enter skip)"),
        ]
        for key, label in fields:
            val = input(f"  {label}: ").strip()
            if val: info[key] = val

        console.print("[yellow]Experience (format: Title@Company|Duration|Bullet1,Bullet2):[/yellow]")
        console.print("[dim]Example: React Dev@TechCorp|2022-Present|Built apps,Led team[/dim]")
        exps = []
        while True:
            e = input("  Experience (Enter to skip): ").strip()
            if not e: break
            parts = e.split("|")
            if len(parts) >= 2:
                tc    = parts[0].split("@")
                exps.append({
                    "title":    tc[0] if tc else e,
                    "company":  tc[1] if len(tc)>1 else "",
                    "duration": parts[1] if len(parts)>1 else "",
                    "bullets":  parts[2].split(",") if len(parts)>2 else [],
                })
        if exps: info["experience"] = exps

        skills_input = input("  Skills (comma separated): ").strip()
        if skills_input:
            info["skills"] = {"technical": [s.strip() for s in skills_input.split(",")]}

        self.voice.speak("CV bana raha hun AI se...")
        r = self.cv.build_cv_from_scratch(info)
        if r["success"]:
            self._render_cv_summary(r["cv"])
            self.voice.speak(f"CV ban gaya! PDF saved.")
            console.print(f"[green]✅ PDF: {r.get('pdf_path','N/A')}[/green]")
        else:
            self.voice.speak(r.get("message","Error"))
        return r.get("pdf_path","")

    def _cv_improve(self, entities, raw) -> str:
        self.voice.speak("CV improve kar raha hun...")
        r = self.cv.improve_cv()
        if r["success"]:
            console.print("[bold]Improvements:[/bold]")
            for imp in r.get("improvements",[])[:5]:
                console.print(f"  ✅ {imp}")
            console.print(f"[green]✅ PDF: {r.get('pdf_path')}[/green]")
            self.voice.speak(f"CV improve ho gaya! {len(r.get('improvements',[]))} improvements.")
        else:
            self.voice.speak(r.get("message","Error"))
        return r.get("pdf_path","")

    def _cv_customize(self, entities, raw) -> str:
        self.voice.speak("Job description paste karein — CV customize karunga...")
        console.print("[yellow]Job description paste karein (phir Enter x2):[/yellow]")
        lines = []
        while True:
            l = input()
            if not l and lines and not lines[-1]:
                break
            lines.append(l)
        jd = "\n".join(lines).strip()
        if not jd:
            self.voice.speak("Job description nahi diya"); return ""

        title = input("Job title: ").strip()
        comp  = input("Company name: ").strip()

        self.voice.speak("CV customize kar raha hun...")
        r = self.cv.customize_for_job(jd, title, comp)
        if r["success"]:
            console.print(Panel(
                f"[bold]ATS Score:[/bold] [green]{r['ats_score']}/100[/green]\n"
                f"[bold]Match:[/bold] {r['match_percentage']}%\n"
                f"[bold]Keywords Added:[/bold] {', '.join(r.get('keywords_added',[])[:5])}\n"
                f"[bold]Missing:[/bold] {', '.join(r.get('keywords_missing',[])[:3])}\n\n"
                f"[yellow]{r.get('recommendation','')}[/yellow]",
                title="📄 CV Customized", style="green"
            ))
            console.print(f"[green]✅ PDF: {r.get('pdf_path')}[/green]")
            self.voice.speak(
                f"CV customize ho gaya! ATS score {r['ats_score']} percent."
            )
        else:
            self.voice.speak(r.get("message","Error"))
        return r.get("pdf_path","")

    def _cv_ats(self, entities, raw) -> str:
        self.voice.speak("Job description dijiye — ATS check karunga...")
        jd = input("Job description: ").strip()
        if not jd: return ""
        r  = self.cv.check_ats_score(jd)
        if r["success"]:
            score  = r.get("ats_score", 0)
            color  = "green" if score >= 80 else "yellow" if score >= 60 else "red"
            console.print(Panel(
                f"[bold]ATS Score:[/bold] [{color}]{score}/100[/{color}]\n"
                f"[bold]Will Pass:[/bold] {'✅ Yes' if r.get('will_pass_ats') else '❌ No'}\n\n"
                f"[bold]Found Keywords:[/bold] {', '.join(r.get('found_keywords',[])[:8])}\n"
                f"[bold red]Missing:[/bold red] {', '.join(r.get('missing_keywords',[])[:5])}\n\n"
                f"[bold]Quick Fixes:[/bold]\n"
                + "\n".join(f"  • {f}" for f in r.get("quick_fixes",[])[:4]),
                title="🎯 ATS Analysis", style="blue"
            ))
            self.voice.speak(
                f"ATS Score hai {score} percent. "
                f"{'Pass kar loge!' if r.get('will_pass_ats') else 'Kuch improvements chahiye.'}"
            )
        return str(r.get("ats_score",""))

    def _cover_letter(self, entities, raw) -> str:
        title = input("Job title: ").strip()
        comp  = input("Company: ").strip()
        jd    = input("Job description (short): ").strip()
        self.voice.speak("Cover letter likh raha hun...")
        r = self.cv.generate_cover_letter(title, comp, jd)
        if r["success"]:
            console.print(Panel(
                r["cover_letter"],
                title=f"📝 Cover Letter — {comp}", style="green"
            ))
            console.print(f"[dim]Words: {r['word_count']} | Saved: {r['saved_at']}[/dim]")
            self.voice.speak(f"Cover letter ready! {r['word_count']} words.")
        return r.get("saved_at","")

    def _cv_versions(self, entities, raw) -> str:
        versions = self.cv.list_cv_versions()
        if not versions:
            self.voice.speak("Koi CV versions nahi hain abhi")
            return ""
        t = Table(title="📄 CV Versions", style="blue")
        t.add_column("#"); t.add_column("File"); t.add_column("Created")
        for i, v in enumerate(versions,1):
            t.add_row(str(i), v["filename"], v["created"])
        console.print(t)
        self.voice.speak(f"{len(versions)} CV versions hain!")
        return str(len(versions))

    def _render_cv_summary(self, cv: dict):
        console.print(Panel(
            f"[bold]Name:[/bold] {cv.get('name','')}\n"
            f"[bold]Email:[/bold] {cv.get('email','')}\n"
            f"[bold]Summary:[/bold] {str(cv.get('summary',''))[:100]}...\n"
            f"[bold]Experience:[/bold] {len(cv.get('experience',[]))} roles\n"
            f"[bold]Skills:[/bold] {str(cv.get('skills',''))[:80]}",
            title="✅ CV Created", style="green"
        ))

    # ═══════════════════════════════════════════════════════════
    # JOB HUNTER ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _job_search(self, entities, raw) -> str:
        import re
        sal_m  = re.search(r'(\d+)k', raw.lower())
        salary = int(sal_m.group(1))*1000 if sal_m else None

        query  = (entities.get("fiverr_category")
                  or self._qwords(raw))
        if not query:
            query = input("Kaunsi jobs dhoondni hain? ").strip()

        location = "Pakistan"
        if any(w in raw.lower() for w in ["remote","lahore","karachi","islamabad"]):
            for w in ["Remote","Lahore","Karachi","Islamabad"]:
                if w.lower() in raw.lower():
                    location = w; break

        self.voice.speak(f"{query} jobs dhoond raha hun...")
        r = self.jobs.search_jobs(query, location, salary_min=salary)

        if r["success"] and r["jobs"]:
            t = Table(title=f"💼 Jobs ({r['count']}) — {query}", style="green")
            t.add_column("#", width=3); t.add_column("Title")
            t.add_column("Company");    t.add_column("Salary")
            t.add_column("Match", width=7)
            for i, j in enumerate(r["jobs"][:10], 1):
                t.add_row(
                    str(i), j.get("title","")[:35],
                    j.get("company","")[:20],
                    j.get("salary_range","N/A")[:18],
                    f"{j.get('match_score',0)}%"
                )
            console.print(t)
            self.voice.speak(
                f"{r['count']} jobs mili hain! "
                f"Top job: {r['jobs'][0].get('title','')}"
            )
        else:
            self.voice.speak("Koi job nahi mili")
        return str(r.get("count",0))

    def _govt_opportunities(self, entities, raw) -> str:
        """⭐ Govt Scholarships + Opportunities search."""
        # Category detect
        cat = "all"
        if any(w in raw.lower() for w in
               ["scholarship","scholarships","wazifa"]):
            cat = "scholarship"
        elif any(w in raw.lower() for w in ["job","naukri","position"]):
            cat = "job"
        elif any(w in raw.lower() for w in
                 ["internship","intern","training"]):
            cat = "internship"

        self.voice.speak(
            "Govt scholarships aur opportunities dhoond raha hun — "
            "latest 2025-2026 opportunities..."
        )
        r = self.opt.find_latest_opportunities(cat)

        if r["success"]:
            opps = r.get("opportunities", [])

            if opps:
                t = Table(
                    title=f"🎓 Opportunities Found ({len(opps)})",
                    style="green"
                )
                t.add_column("Title", style="bold", max_width=35)
                t.add_column("Organization", max_width=22)
                t.add_column("Type")
                t.add_column("Amount/Salary", max_width=20)
                t.add_column("Deadline")
                t.add_column("Status")
                for o in opps:
                    status_color = (
                        "green" if "open" in o.get("status","").lower()
                        else "red"
                    )
                    t.add_row(
                        o.get("title","")[:35],
                        o.get("organization","")[:22],
                        o.get("type",""),
                        o.get("amount","N/A")[:20],
                        o.get("deadline","N/A"),
                        f"[{status_color}]{o.get('status','?')}[/{status_color}]"
                    )
                console.print(t)

                # Tips
                tips = r.get("tips", [])
                if tips:
                    console.print("\n[bold cyan]💡 Tips:[/bold cyan]")
                    for tip in tips[:3]:
                        console.print(f"  ✅ {tip}")

                total = len(opps)
                self.voice.speak(
                    f"{total} opportunities mili hain! "
                    f"Kisi pe apply karna hai? 'govt apply karo' bolein."
                )
            else:
                self.voice.speak(
                    "Abhi koi open opportunity nahi mili. API key set karein better results ke liye."
                )

            console.print(
                "\n[yellow]Kisi opportunity pe apply karna hai? "
                "'govt apply karo' bolein[/yellow]"
            )
        else:
            self.voice.speak("Opportunities fetch nahi ho sake — API key check karein")

        return str(len(r.get("opportunities", [])))

    def _govt_apply(self, entities, raw) -> str:
        """Govt opportunity pe apply karo — CV customize + submit."""
        self.voice.speak(
            "Kaunsi opportunity pe apply karna hai? "
            "Details dijiye..."
        )
        console.print("[cyan]Opportunity details:[/cyan]")

        opp_name   = input("  Opportunity name: ").strip()
        apply_url  = input("  Apply URL: ").strip()
        opp_type   = input("  Type (scholarship/job/internship): ").strip() or "scholarship"
        eligibility = input("  Kya aap eligible hain? (y/n): ").strip().lower()

        if eligibility != 'y':
            self.voice.speak("Aap eligible nahi hain is opportunity ke liye")
            return "not_eligible"

        opp = {
            "name":      opp_name,
            "type":      opp_type,
            "apply_url": apply_url,
        }

        # CV customize karo?
        self.voice.speak("Kya CV is opportunity ke liye customize karun?")
        if self._ok("CV customize karein?"):
            jd = input("Job/Scholarship requirements (paste karein): ").strip()
            if jd:
                cv_r = self.cv.customize_for_job(jd, opp_name, "Government")
                cv_path = cv_r.get("pdf_path","")
                self.voice.speak(
                    f"CV customize ho gaya! ATS Score: {cv_r.get('ats_score',0)}%"
                )
            else:
                cv_path = ""
        else:
            cv_path = ""

        # Cover letter?
        cover_letter = ""
        self.voice.speak("Cover letter banaun?")
        if self._ok("Cover letter generate karein?"):
            cl_r = self.cv.generate_cover_letter(
                opp_name, "Government of Pakistan",
                f"Applying for {opp_name}"
            )
            cover_letter = cl_r.get("cover_letter","")
            if cover_letter:
                console.print(Panel(
                    cover_letter[:500] + "...",
                    title="📝 Cover Letter Preview", style="green"
                ))

        # Apply
        self.voice.speak("Apply kar raha hun...")
        r = self.jobs.apply_to_opportunity(opp, cv_path, cover_letter)

        if r["success"]:
            console.print(Panel(
                f"[bold]Opportunity:[/bold] {opp_name}\n"
                f"[bold]Method:[/bold] {r.get('method','')}\n"
                f"[bold]App ID:[/bold] {r.get('app_id','')}\n\n"
                + (r.get("instructions","") or r.get("message","")),
                title="✅ Application Submitted", style="green"
            ))
            self.voice.speak(
                f"Application submit ho gayi! "
                f"Track ID: {r.get('app_id','')}. "
                f"1 hafte baad follow-up reminder set kar diya."
            )
        return r.get("app_id","")

    def _job_apply(self, entities, raw) -> str:
        """Regular job apply."""
        title    = input("Job title: ").strip()
        company  = input("Company: ").strip()
        url      = input("Apply URL: ").strip()
        opp      = {"title": title, "company": company,
                    "apply_url": url, "type": "job"}

        self.voice.speak("Apply kar raha hun...")
        r = self.jobs.apply_to_opportunity(opp)
        if r["success"]:
            console.print(f"[green]✅ {r.get('message','')}[/green]")
            self.voice.speak(f"Application submitted! ID: {r.get('app_id','')}")
        return r.get("app_id","")

    def _job_followup(self, entities, raw) -> str:
        due = self.jobs.get_followup_due()
        if not due:
            self.voice.speak("Koi follow-up due nahi hai abhi")
            return "none"
        t = Table(title=f"📬 Follow-ups Due ({len(due)})", style="yellow")
        t.add_column("Title"); t.add_column("Company"); t.add_column("Applied")
        for a in due:
            t.add_row(a.get("title",""), a.get("company",""),
                      a.get("applied_at","")[:10])
        console.print(t)
        self.voice.speak(
            f"{len(due)} applications ka follow-up karna hai!"
        )
        return str(len(due))

    def _job_status(self, entities, raw) -> str:
        stats = self.jobs.get_stats()
        console.print(Panel(
            f"[bold]Total Applications:[/bold] {stats['total']}\n"
            f"[green]Applied:[/green] {stats['applied']}\n"
            f"[cyan]Interviews:[/cyan] {stats['interview']}\n"
            f"[yellow]Offers:[/yellow] {stats['offered']}\n"
            f"[red]Rejected:[/red] {stats['rejected']}\n"
            f"[yellow]Follow-up Due:[/yellow] {stats['followup_due']}",
            title="📊 Job Applications", style="blue"
        ))
        self.voice.speak(
            f"Total {stats['total']} applications. "
            f"{stats['followup_due']} follow-ups due."
        )
        return str(stats['total'])

    # ═══════════════════════════════════════════════════════════
    # SOCIAL MEDIA ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _content_create(self, entities, raw) -> str:
        topic    = self._qwords(raw) or input("Content topic: ").strip()
        platform = "tiktok"
        for p in ["tiktok","instagram","youtube","linkedin","facebook"]:
            if p in raw.lower(): platform = p; break

        self.voice.speak(f"{platform} ke liye content bana raha hun...")
        r = self.social.create_content(topic, platform)
        if r["success"]:
            c = r["content"]
            console.print(Panel(
                f"[bold]Title:[/bold] {c.get('title','')}\n\n"
                f"[bold red]🎬 HOOK (first 3 sec):[/bold red]\n{c.get('hook','')}\n\n"
                f"[bold]Full Script:[/bold]\n"
                + "\n".join(
                    f"[{s.get('time','')}] {s.get('text','')} → {s.get('action','')}"
                    for s in c.get("script",[])
                ) +
                f"\n\n[bold]Thumbnail:[/bold] {c.get('thumbnail_text','')}\n"
                f"[bold]Viral Score:[/bold] {c.get('viral_score',0)}/100",
                title=f"🎬 {platform.upper()} Content", style="green"
            ))
            console.print(
                f"[cyan]Hashtags:[/cyan] "
                f"{' '.join(c.get('hashtags',[])[:10])}"
            )
            self.voice.speak(
                f"Content ready! Viral score {c.get('viral_score',0)}/100. "
                f"Hook: {c.get('hook','')[:50]}"
            )
        return r.get("saved_at","")

    def _hashtags(self, entities, raw) -> str:
        topic = self._qwords(raw) or input("Topic: ").strip()
        plat  = "tiktok"
        for p in self.social.PLATFORMS:
            if p in raw.lower(): plat = p; break
        self.voice.speak(f"30 hashtags generate kar raha hun...")
        r = self.social.generate_hashtags(topic, plat, 30)
        if r["success"]:
            console.print(Panel(
                f"[bold]Copy-Paste:[/bold]\n{r.get('copy_paste','')}\n\n"
                f"[bold]Top 5:[/bold] {' '.join(r.get('top_5',[]))}\n\n"
                f"[dim]{r.get('strategy','')}[/dim]",
                title=f"🏷️ {len(r.get('hashtags',[]))} Hashtags", style="green"
            ))
            self.voice.speak(f"{len(r.get('hashtags',[]))} hashtags ready!")
        return topic

    def _trending(self, entities, raw) -> str:
        niche = self._qwords(raw) or input("Aapka niche (optional): ").strip()
        self.voice.speak("Trending topics fetch kar raha hun...")
        r = self.social.get_trending_topics(niche)
        if r["success"]:
            t = Table(title="🔥 Trending Topics", style="red")
            t.add_column("Topic"); t.add_column("Score", width=7)
            t.add_column("Best Platform"); t.add_column("Urgency")
            for tp in r.get("trending_topics",[])[:8]:
                t.add_row(
                    tp.get("topic","")[:35],
                    str(tp.get("trend_score",0)),
                    tp.get("best_platform",""),
                    tp.get("urgency","")[:20]
                )
            console.print(t)
            console.print(
                f"[yellow]💡 {r.get('best_niche_opportunity','')}[/yellow]"
            )
            top = r.get("trending_topics",[{}])[0].get("topic","")
            self.voice.speak(
                f"Top trending: {top}! Jaldi content banao."
            )
        return niche

    def _content_calendar(self, entities, raw) -> str:
        niche = input("Aapka niche: ").strip() or "tech/coding"
        self.voice.speak("7 days ka content calendar bana raha hun...")
        r = self.social.create_content_calendar(niche, days=7)
        if r.get("calendar"):
            t = Table(title="📅 7-Day Content Calendar", style="blue")
            t.add_column("Day"); t.add_column("Platform")
            t.add_column("Topic"); t.add_column("Time")
            for day in r["calendar"]:
                for post in day.get("posts",[]):
                    t.add_row(
                        f"Day {day['day']} ({day.get('date','')[:3]})",
                        post.get("platform",""),
                        post.get("topic","")[:35],
                        post.get("time","")
                    )
            console.print(t)
            console.print(
                f"[cyan]Weekly Reach: {r.get('estimated_weekly_reach','')}[/cyan]"
            )
            self.voice.speak("7 days ka calendar ready!")
        return r.get("saved_at","")

    def _caption(self, entities, raw) -> str:
        topic = self._qwords(raw) or input("Caption topic: ").strip()
        plat  = "instagram"
        for p in self.social.PLATFORMS:
            if p in raw.lower(): plat = p; break
        r = self.social.write_caption(topic, plat)
        console.print(Panel(
            r.get("caption",""), title=f"✍️ {plat} Caption", style="green"
        ))
        self.voice.speak("Caption ready!")
        return r.get("caption","")

    def _viral_score(self, entities, raw) -> str:
        idea = input("Content idea describe karein: ").strip()
        r    = self.social.analyze_viral_potential(idea)
        score = r.get("viral_score",0)
        color = "green" if score>=75 else "yellow" if score>=50 else "red"
        console.print(Panel(
            f"[bold]Viral Score:[/bold] [{color}]{score}/100[/{color}]\n\n"
            f"[bold]Improvements:[/bold]\n"
            + "\n".join(f"  • {i}" for i in r.get("improvements",[])[:4]),
            title="🎯 Viral Potential", style="blue"
        ))
        self.voice.speak(f"Viral score hai {score}/100!")
        return str(score)

    def _social_report(self, entities, raw) -> str:
        self.voice.speak("Social media growth report bana raha hun...")
        r = self.social.generate_growth_report()
        rep = r.get("report",{})
        console.print(Panel(
            f"[bold]Overall Score:[/bold] {rep.get('overall_score',0)}/100\n"
            f"[bold]Best Time:[/bold] {rep.get('best_posting_time','')}\n\n"
            + "\n".join(
                f"  📌 {rec}"
                for rec in rep.get("growth_recommendations",[])[:4]
            ),
            title="📈 Social Media Report", style="green"
        ))
        self.voice.speak("Growth report ready!")
        return r.get("saved_at","")

    def _competitor_social(self, entities, raw) -> str:
        handle = input("Competitor ka handle (@username): ").strip().lstrip("@")
        plat   = "tiktok"
        for p in self.social.PLATFORMS:
            if p in raw.lower(): plat = p; break
        r = self.social.analyze_competitor(handle, plat)
        if r["success"]:
            console.print(Panel(
                f"[bold]Followers:[/bold] {r.get('estimated_followers','')}\n"
                f"[bold]Strategy:[/bold] {r.get('content_strategy','')}\n"
                f"[bold]Engagement:[/bold] {r.get('engagement_rate','')}\n\n"
                f"[bold green]Opportunities for You:[/bold green]\n"
                + "\n".join(f"  ✅ {o}" for o in r.get("opportunities_for_you",[])) +
                f"\n\n[bold yellow]Differentiate:[/bold yellow] {r.get('recommended_differentiation','')}",
                title=f"📊 @{handle} Analysis", style="blue"
            ))
            self.voice.speak("Competitor analysis ready!")
        return handle

    # ═══════════════════════════════════════════════════════════
    # WEBSITE MANAGER ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _blog_write(self, entities, raw) -> str:
        topic = self._qwords(raw) or input("Blog topic: ").strip()
        self.voice.speak(f"{topic} pe SEO blog likh raha hun...")
        r = self.website.generate_blog_post(topic)
        if r["success"]:
            meta = r.get("meta",{})
            console.print(Panel(
                f"[bold]Title:[/bold] {meta.get('title','')}\n"
                f"[bold]Description:[/bold] {meta.get('description','')}\n"
                f"[bold]SEO Score:[/bold] {r.get('seo_score',0)}/100\n"
                f"[bold]Reading Time:[/bold] {meta.get('reading_time','')}\n\n"
                f"[dim]React: {r.get('react_path','N/A')}[/dim]",
                title="📝 Blog Post Ready", style="green"
            ))
            self.voice.speak(
                f"Blog post ready! SEO score {r.get('seo_score',0)}/100."
            )
        return r.get("react_path","")

    def _service_page(self, entities, raw) -> str:
        service = self._qwords(raw) or input("Service name: ").strip()
        self.voice.speak(f"{service} service page bana raha hun...")
        r = self.website.generate_service_page(service)
        if r["success"]:
            console.print(Panel(
                f"[bold]Service:[/bold] {service}\n"
                f"[bold]SEO Score:[/bold] {r.get('seo_score',0)}/100\n"
                f"[bold]File:[/bold] {r.get('react_path','')}",
                title="🌐 Service Page", style="green"
            ))
            self.voice.speak(f"Service page ready! File save ho gaya.")
        return r.get("react_path","")

    def _seo_check(self, entities, raw) -> str:
        self.voice.speak("Page content dijiye — SEO check karunga...")
        content = input("Page content (paste karein): ").strip()
        keyword = input("Target keyword: ").strip()
        r = self.website.check_seo_score(content, keyword)
        if r["success"]:
            score = r.get("overall_score",0)
            color = "green" if score>=80 else "yellow" if score>=60 else "red"
            console.print(Panel(
                f"[bold]SEO Score:[/bold] [{color}]{score}/100[/{color}]\n\n"
                f"[bold red]Issues:[/bold red]\n"
                + "\n".join(f"  ❌ {i}" for i in r.get("critical_issues",[])[:3]) +
                "\n\n[bold green]Quick Wins:[/bold green]\n"
                + "\n".join(f"  ✅ {w}" for w in r.get("quick_wins",[])[:4]),
                title="🔍 SEO Analysis", style="blue"
            ))
            self.voice.speak(f"SEO score hai {score}/100.")
        return str(r.get("overall_score",""))

    def _git_push(self, entities, raw) -> str:
        path = input("Website folder path (Enter for current): ").strip() or "."
        msg  = input("Commit message (Enter for auto): ").strip()
        r    = self.website.git_commit_push(message=msg or None,
                                             website_path=path)
        if r["success"]:
            self.voice.speak("Code push ho gaya!")
        else:
            self.voice.speak(r.get("message","Git error"))
            console.print(f"[red]{r.get('message','')}[/red]")
        return r.get("message","")

    def _website_generate(self, entities, raw) -> str:
        req = input("Website requirements describe karein: ").strip()
        if not req: return ""
        self.voice.speak("Website plan generate kar raha hun...")
        r = self.website.generate_full_website(req)
        if r["success"]:
            plan = r["plan"]
            console.print(Panel(
                f"[bold]Tech Stack:[/bold]\n"
                + "\n".join(
                    f"  {k}: {v}"
                    for k,v in plan.get("tech_stack",{}).items()
                ) +
                f"\n\n[bold]Setup Commands:[/bold]\n"
                + "\n".join(
                    f"  $ {c}"
                    for c in plan.get("setup_commands",[])[:4]
                ) +
                f"\n\n[bold]Time:[/bold] {plan.get('estimated_time','')}",
                title="💻 Website Plan", style="green"
            ))
            self.voice.speak("Website plan ready!")
        return r.get("saved_at","")

    # ═══════════════════════════════════════════════════════════
    # CLIENT MANAGER ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _client_add(self, entities, raw) -> str:
        name  = self._person(raw) or input("Client name: ").strip()
        email = input("Email: ").strip()
        phone = input("Phone: ").strip()
        comp  = input("Company (optional): ").strip()
        r = self.clients.add_client(name, email, phone, comp)
        self.voice.speak(r["message"])
        return r.get("client_id","")

    def _client_status(self, entities, raw) -> str:
        name = self._person(raw) or input("Client name: ").strip()
        r    = self.clients.get_client_status(name)
        if r["success"]:
            c = r["client"]
            console.print(Panel(
                f"[bold]Client:[/bold] {c['name']}\n"
                f"[bold]Email:[/bold] {c.get('email','')}\n"
                f"[bold]Active Projects:[/bold] {len(r['active_projects'])}\n"
                f"[bold]Pending Invoices:[/bold] {len(r['pending_invoices'])}\n"
                f"[bold]Total Earned:[/bold] PKR {c.get('total_earned',0):,.0f}\n\n"
                f"[yellow]{r.get('summary','')}[/yellow]",
                title=f"👤 {c['name']} Status", style="blue"
            ))
            self.voice.speak(r.get("summary",""))
        else:
            self.voice.speak(r.get("message","Client nahi mila"))
        return name

    def _invoice_create(self, entities, raw) -> str:
        client = self._person(raw) or input("Client name: ").strip()
        items  = []
        console.print("[yellow]Items add karein (Enter to finish):[/yellow]")
        while True:
            desc = input("  Description (Enter to finish): ").strip()
            if not desc: break
            try:
                qty  = int(input("  Quantity (default 1): ").strip() or "1")
                rate = float(input("  Rate (PKR): ").strip())
                items.append({"description": desc, "qty": qty, "rate": rate})
            except ValueError:
                console.print("[red]Invalid input[/red]")

        if not items:
            self.voice.speak("Koi items nahi diye")
            return ""

        r = self.clients.create_invoice(client, items)
        if r["success"]:
            console.print(Panel(
                f"[bold]Invoice:[/bold] {r['invoice_number']}\n"
                f"[bold]Total:[/bold] [green]{r['total']}[/green]\n"
                f"[bold]Due:[/bold] {r['due_date']}\n"
                f"[bold]PDF:[/bold] {r['pdf_path']}",
                title="💰 Invoice Created", style="green"
            ))
            self.voice.speak(
                f"Invoice ready! Total {r['total']}. Due date {r['due_date']}."
            )
        return r.get("invoice_number","")

    def _proposal(self, entities, raw) -> str:
        client = self._person(raw) or input("Client name: ").strip()
        desc   = input("Project description: ").strip()
        budget = input("Budget range (optional): ").strip()
        self.voice.speak("Proposal likh raha hun...")
        r = self.clients.generate_proposal(client, desc, budget)
        if r["success"]:
            console.print(Panel(
                r["proposal"][:800] + "...\n[dim](Full proposal saved)[/dim]",
                title="📋 Project Proposal", style="green"
            ))
            console.print(f"[dim]Saved: {r['saved_at']}[/dim]")
            self.voice.speak("Proposal ready! File save ho gaya.")
        return r.get("saved_at","")

    def _payment_track(self, entities, raw) -> str:
        overdue = self.clients.get_overdue_invoices()
        stats   = self.clients.get_all_stats()
        console.print(Panel(
            f"[bold]Total Clients:[/bold] {stats['total_clients']}\n"
            f"[bold]Active Projects:[/bold] {stats['active_projects']}\n"
            f"[bold]Total Earned:[/bold] PKR {stats['total_earned']:,.0f}\n"
            f"[bold red]Overdue Invoices:[/bold red] {stats['overdue_invoices']}",
            title="💳 Payment Dashboard", style="blue"
        ))
        if overdue:
            t = Table(title="⚠️ Overdue", style="red")
            t.add_column("Client"); t.add_column("Invoice")
            t.add_column("Amount"); t.add_column("Days Late")
            for o in overdue:
                t.add_row(o["client"], o["invoice"],
                          f"{o['currency']} {o['total']:,.0f}",
                          str(o["days_overdue"]))
            console.print(t)
            self.voice.speak(
                f"{len(overdue)} overdue invoices hain! "
                f"Clients ko remind karo."
            )
        else:
            self.voice.speak("Koi overdue invoice nahi! Sab clear hai.")
        return str(stats['overdue_invoices'])

    def _disk_cleanup(self, entities, raw) -> str:
        self.voice.speak("C drive analyze kar raha hun...")
        r = self.clients.analyze_disk_space("C")
        if r["success"]:
            console.print(Panel(
                f"[bold]Drive C:[/bold]\n"
                f"  Total: {r['total']}\n"
                f"  Used:  {r['used']}\n"
                f"  Free:  {r['free']}\n"
                f"  Usage: {r['percent']}\n\n"
                + (
                    "[bold yellow]Safe to Clean:[/bold yellow]\n"
                    + "\n".join(
                        f"  • {c['type']}: {c['size']} ({c['files']} files)"
                        for c in r.get("cleanable",[])
                    )
                    if r.get("cleanable") else "Nothing to clean right now"
                ),
                title="🧹 Disk Analysis", style="blue"
            ))
            self.voice.speak(
                f"C drive {r['percent']} use ho raha hai. "
                f"{len(r.get('cleanable',[]))} folders clean ho sakti hain."
            )
        else:
            self.voice.speak(r.get("message","Error"))
        return r.get("percent","")

    # ═══════════════════════════════════════════════════════════
    # UPDATED WELCOME + HELP
    # ═══════════════════════════════════════════════════════════

    def _show_welcome(self):
        t = Text()
        t.append("🤖 ARIA v3 FINAL\n", style="bold cyan")
        t.append("Phase 1 ✅ + Phase 2 ✅ + Phase 3 ✅\n", style="green")
        t.append("Urdu • English • Roman Urdu\n", style="yellow")
        console.print(Panel(t, style="cyan"))
        s = self.memory.get_stats()
        cs = self.clients.get_all_stats()
        console.print(
            f"[dim]Conversations:{s['total_conversations']} | "
            f"Contacts:{s['total_contacts']} | "
            f"Emails:{s['emails_sent']} | "
            f"WA:{s['whatsapp_sent']} | "
            f"Clients:{cs['total_clients']}[/dim]\n"
        )
        self.voice.speak(
            "Salam! ARIA v3 ready — Phase 1, 2, aur 3 sab active. "
            "Help ke liye 'help' likhein."
        )

    def _show_capabilities(self):
        console.print(
            "[bold cyan]Phase 1:[/bold cyan] Files • Apps • System • Screenshots • Email Draft\n"
            "[bold green]Phase 2:[/bold green] WhatsApp • Gmail Full • Fiverr Engine • Scheduler\n"
            "[bold yellow]Phase 3:[/bold yellow]\n"
            "  📄 CV: banao • improve • customize • ATS check • cover letter\n"
            "  💼 Jobs: search • apply • track • follow-up\n"
            "  🏛️ Govt: scholarships • opportunities • apply\n"
            "  📱 Social: content • hashtags • trending • calendar • viral score\n"
            "  🌐 Website: blog • service page • SEO • git push\n"
            "  👥 Clients: add • invoice • proposal • payment track\n"
            "  🧹 Laptop: C drive cleanup\n"
        )


def main():
    import argparse
    p = argparse.ArgumentParser(description="ARIA v3 FINAL")
    p.add_argument("--voice", "-v", action="store_true")
    args = p.parse_args()
    ARIAv3().run(use_voice=args.voice)


if __name__ == "__main__":
    main()
