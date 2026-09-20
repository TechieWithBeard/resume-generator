"""
LinkedIn Job Extractor Service.
Scrapes and parses job descriptions from LinkedIn job postings with structured extraction and graceful bot-wall fallbacks.
"""

import json
import re
from typing import Any, Dict, Optional
import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class LinkedInExtractor:
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]

    @staticmethod
    def extract_job_id(url: str) -> Optional[str]:
        """Extracts job ID from various LinkedIn URL formats."""
        patterns = [
            r"/jobs/view/(?:[a-zA-Z0-9\-]+-)?(\d+)",
            r"currentJobId=(\d+)",
            r"jobId=(\d+)",
            r"/jobs/collections/recommended/\?currentJobId=(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Attempts to scrape job details from LinkedIn URL.
        Returns a dict with:
          success: bool
          title: Optional[str]
          company: Optional[str]
          location: Optional[str]
          job_description: str
          raw_text: str
          error: Optional[str]
          requires_manual_paste: bool
        """
        if not url or "linkedin.com" not in url.lower():
            return {
                "success": False,
                "error": "Invalid URL. Please provide a valid LinkedIn job posting URL.",
                "requires_manual_paste": False,
            }

        headers = {
            "User-Agent": self.USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
        }

        # Normalize URL to standard public job view if job ID is detected
        job_id = self.extract_job_id(url)
        target_url = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else url

        try:
            response = requests.get(target_url, headers=headers, timeout=12, allow_redirects=True)
            
            # Handle LinkedIn authwall redirect or bot challenge
            if response.status_code in (403, 429) or "authwall" in response.url.lower():
                return {
                    "success": False,
                    "error": (
                        "LinkedIn is requiring authentication or presented an authwall for automated requests. "
                        "Please copy and paste the Job Description text directly into the 'Job Content' tab."
                    ),
                    "requires_manual_paste": True,
                    "job_id": job_id,
                }

            response.raise_for_status()
            html_text = response.text

            if BeautifulSoup is not None:
                soup = BeautifulSoup(response.content, "html.parser")
            else:
                soup = None

            # 1. Try JSON-LD structured metadata
            title = None
            company = None
            description = None
            location = None

            if soup is not None:
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string or "")
                        if isinstance(data, dict) and data.get("@type") == "JobPosting":
                            title = data.get("title")
                            company = data.get("hiringOrganization", {}).get("name")
                            description = data.get("description")
                            job_loc = data.get("jobLocation", {})
                            if isinstance(job_loc, dict):
                                addr = job_loc.get("address", {})
                                if isinstance(addr, dict):
                                    location = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', '')}".strip(", ")
                            break
                    except Exception:
                        continue

                # 2. Extract DOM elements if JSON-LD missing
                if not title:
                    title_elem = soup.find(["h1", "h2"], class_=re.compile(r"topcard__title|job-title|top-card-layout__title", re.I))
                    if title_elem:
                        title = title_elem.get_text(strip=True)

                if not company:
                    company_elem = soup.find(["a", "span"], class_=re.compile(r"topcard__org-name|topcard__flavor--black-link|sub-nav-cta__sub-title", re.I))
                    if company_elem:
                        company = company_elem.get_text(strip=True)

                if not description:
                    desc_elem = soup.find("div", class_=re.compile(r"show-more-less-html__markup|description__text", re.I))
                    if desc_elem:
                        description = desc_elem.get_text(separator="\n", strip=True)

                if not description:
                    meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
                    if meta_desc and meta_desc.get("content"):
                        description = meta_desc["content"]

                if not description:
                    for s in soup(["script", "style", "nav", "footer", "header"]):
                        s.extract()
                    description = soup.get_text(separator="\n", strip=True)
            else:
                # Regex fallback when bs4 is not present
                json_ld_matches = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', html_text, re.DOTALL | re.IGNORECASE)
                for raw_json in json_ld_matches:
                    try:
                        data = json.loads(raw_json)
                        if isinstance(data, dict) and data.get("@type") == "JobPosting":
                            title = data.get("title")
                            company = data.get("hiringOrganization", {}).get("name")
                            description = data.get("description")
                            break
                    except Exception:
                        continue

                if not title:
                    title_m = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.IGNORECASE)
                    if title_m:
                        title = title_m.group(1).split('|')[0].strip()

                if not description:
                    desc_m = re.search(r'<meta[^>]+(?:name|property)=[\'"](?:og:description|description)[\'"][^>]+content=[\'"](.*?)[\'"]', html_text, re.IGNORECASE)
                    if desc_m:
                        description = desc_m.group(1)

            if not description or len(description.strip()) < 50:
                return {
                    "success": False,
                    "error": "Could not extract full job content from this page. Please paste the job description directly.",
                    "requires_manual_paste": True,
                }

            # Clean and truncate if excessively large
            clean_desc = re.sub(r"\n{3,}", "\n\n", description).strip()
            if len(clean_desc) > 8000:
                clean_desc = clean_desc[:8000] + "\n...[truncated]"

            return {
                "success": True,
                "title": title or "Target Role",
                "company": company or "Target Company",
                "location": location or "",
                "job_description": clean_desc,
                "job_id": job_id,
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "LinkedIn request timed out. Please paste the job content directly.",
                "requires_manual_paste": True,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to extract from LinkedIn: {str(e)}. Please paste the job description directly.",
                "requires_manual_paste": True,
            }


linkedin_extractor = LinkedInExtractor()
