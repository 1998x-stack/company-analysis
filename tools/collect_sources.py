#!/usr/bin/env python3
"""Explicit HTTPS filing acquisition with size, host, and redirect protections.

Fetch verifies transport bytes and hashes, not factual correctness or copyright.
Network access is disabled unless the caller expressly invokes fetch().
"""
import hashlib,html.parser,ipaddress,socket
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,build_opener,HTTPRedirectHandler

class DenyRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError("HTTP redirects are disabled; verify each source URL")

def validate_url(url,allowed_hosts):
    parsed=urlparse(url)
    if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        raise ValueError("An absolute HTTPS URL with default port is required")
    if parsed.hostname.lower() not in {h.lower() for h in allowed_hosts}:
        raise ValueError("Host is not on the explicit allowlist")
    # Prevent requests to loopback/private/link-local/reserved addresses.
    for info in socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM):
        address=ipaddress.ip_address(info[4][0])
        if not address.is_global:
            raise ValueError("Non-public source IP refused")
    return parsed

def fetch(url,allowed_hosts,max_bytes=8_000_000):
    validate_url(url,allowed_hosts)
    req=Request(url,headers={"User-Agent":"CompanyAnalysisResearch/0.1","Accept":"application/pdf,text/html,text/plain"})
    resp=build_opener(DenyRedirect()).open(req,timeout=15)
    try:
        if resp.status!=200:raise ValueError("Unsuccessful HTTP status")
        content_type=resp.headers.get_content_type()
        if content_type not in ("application/pdf","text/html","text/plain","application/octet-stream"):
            raise ValueError("Unsupported source media type")
        data=resp.read(max_bytes+1)
        if len(data)>max_bytes:raise ValueError("Source exceeds byte limit")
        return {"content":data,"sha256":hashlib.sha256(data).hexdigest(),
                "media_type":content_type,"source_url":url}
    finally:
        resp.close()

class TextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript") and self.skip:self.skip-=1
    def handle_data(self,value):
        if not self.skip and value.strip():self.parts.append(value.strip())

def extract_text(content,media_type):
    if media_type=="application/pdf" or content.startswith(b"%PDF-"):
        try:
            from pypdf import PdfReader
        except ImportError as err:
            raise RuntimeError("pip install pypdf to extract PDFs") from err
        from io import BytesIO
        reader=PdfReader(BytesIO(content))
        if len(reader.pages)>400:
            raise ValueError("PDF too long for this extraction profile")
        return "\n\n".join(f"PAGE {i+1}\n{page.extract_text() or ''}"
                           for i,page in enumerate(reader.pages))
    text=content.decode("utf-8",errors="replace")
    if media_type=="text/html" or "<html" in text[:200].lower():
        parser=TextExtractor();parser.feed(text)
        return "\n".join(parser.parts)
    return text

def main():
    """Explicit network opt-in: never run mass discovery by default."""
    import argparse,json
    from datetime import date
    p=argparse.ArgumentParser()
    p.add_argument("--url",required=True)
    p.add_argument("--allowed-host",action="append",required=True)
    p.add_argument("--allow-network",action="store_true")
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    if not args.allow_network:
        raise SystemExit("Explicit --allow-network is required")
    result=fetch(args.url,args.allowed_host)
    suffix=".pdf" if result["content"].startswith(b"%PDF-") else ".html"
    args.output_dir.mkdir(parents=True,exist_ok=True)
    output=args.output_dir/(result["sha256"]+suffix)
    if output.exists() and output.read_bytes()!=result["content"]:
        raise ValueError("Content-addressed file collision")
    output.write_bytes(result["content"])
    meta={"url":args.url,"sha256":result["sha256"],
          "media_type":result["media_type"],"retrieved_at":date.today().isoformat(),
          "local_path":str(output),"verification_status":"retrieved_not_fact_checked"}
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
