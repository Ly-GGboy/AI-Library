 #!/usr/bin/env python
import asyncio
from app.services.meilisearch_service import MeiliSearchService

async def main():
    service = MeiliSearchService()
    print("[INFO] 开始构建索引...")
    result = await service.build_index()
    print(f"[INFO] 索引构建结果: {result}")

if __name__ == "__main__":
    asyncio.run(main())