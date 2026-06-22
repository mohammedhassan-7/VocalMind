import asyncio
import re
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.core.database import engine
from app.models.policy import CompanyPolicy
from app.models.faq import FAQArticle

def _clean_title(title: str) -> str:
    if not title:
        return ""
    clean = re.sub(r'(?i)^(nexalink telecommunications|meridian)[ -]*(policy|sop)?\s*:?\s*', '', title)
    clean = re.sub(r'(?i)^policy\s*:?\s*', '', clean)
    clean = re.sub(r'(?i)^sop\s*\d*\s*:?\s*', '', clean)
    clean = re.sub(r'(?i)^kb\s*\d*\s*:?\s*', '', clean)
    return clean.strip() or title

def _clean_preview(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'#+', '', text)
    clean = re.sub(r'[*_]{1,2}(.*?)[*_]{1,2}', r'\1', clean)
    clean = clean.replace('|', ' ')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

async def main():
    async with AsyncSession(engine) as session:
        # Update Policies
        result = await session.exec(select(CompanyPolicy))
        for p in result.all():
            p.policy_title = _clean_title(p.policy_title)
            p.policy_text = _clean_preview(p.policy_text)
            session.add(p)
            
        # Update FAQs and KB
        result2 = await session.exec(select(FAQArticle))
        for f in result2.all():
            f.question = _clean_title(f.question)
            f.answer = _clean_preview(f.answer)
            session.add(f)
            
        await session.commit()
        print("Database updated!")

if __name__ == "__main__":
    asyncio.run(main())
