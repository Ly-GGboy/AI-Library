#!/usr/bin/env python
from meilisearch_python_sdk import AsyncClient
import asyncio

async def test():
    async with AsyncClient('http://localhost:7700', 'masterKey') as client:
        # 测试健康状态
        print("\n=== 测试健康状态 ===")
        health = await client.health()
        print(f'Health Status: {health.status}')
        
        # 测试索引操作
        print("\n=== 测试索引操作 ===")
        index_name = "documents"
        try:
            # 获取或创建索引
            indexes = await client.get_indexes()
            print(f"获取到的索引列表: {indexes}")
            
            # 检查索引是否存在
            index_exists = False
            if indexes:
                index_exists = any(index.uid == index_name for index in indexes)
            
            if not index_exists:
                print(f"创建索引: {index_name}")
                await client.create_index(index_name)
            
            index = await client.get_index(index_name)
            print(f"获取到索引: {index_name}")
            
            # 设置可过滤属性
            print("\n设置可过滤属性...")
            await index.update_filterable_attributes(['type'])
            
            # 设置可排序属性
            print("\n设置可排序属性...")
            await index.update_sortable_attributes(['name'])
            
            # 添加测试文档
            test_docs = [
                {
                    "id": "test1",
                    "name": "测试文档1.md",
                    "content": "这是一个测试文档的内容",
                    "type": "md"
                },
                {
                    "id": "test2",
                    "name": "测试文档2.md",
                    "content": "这是另一个测试文档",
                    "type": "md"
                }
            ]
            
            print("\n添加测试文档...")
            task = await index.add_documents(test_docs)
            print("等待索引更新...")
            await client.wait_for_task(task.task_uid)  # 使用内置的 wait_for_task
            
            # 测试基本搜索
            print("\n=== 测试基本搜索 ===")
            query = "测试"
            print(f"\n1. 使用字符串查询: search('{query}')")
            # 将查询字符串作为第一个位置参数传递
            results = await index.search(query)
            print(f"结果内容: {results}")
            
            # 测试带选项的搜索
            print("\n2. 使用查询和选项")
            print(f"搜索参数: limit=5, offset=0, attributes_to_retrieve=['id', 'name', 'content', 'type']")
            results = await index.search(
                query,  # 查询字符串作为第一个位置参数
                limit=5,
                offset=0,
                attributes_to_retrieve=["id", "name", "content", "type"]
            )
            print(f"结果内容: {results}")
            
            # 测试不同的搜索选项组合
            print("\n3. 测试不同的搜索选项组合")
            
            # 测试带过滤的搜索
            print("\n3.1 带过滤的搜索: filter='type = md'")
            results = await index.search(
                query,  # 查询字符串作为第一个位置参数
                filter="type = md",
                limit=5,
                attributes_to_retrieve=["id", "name", "content", "type"]
            )
            print(f"过滤搜索结果: {results}")
            
            # 测试带排序的搜索
            print("\n3.2 带排序的搜索: sort=['name:asc']")
            results = await index.search(
                query,  # 查询字符串作为第一个位置参数
                sort=["name:asc"],
                limit=5,
                attributes_to_retrieve=["id", "name", "content", "type"]
            )
            print(f"排序搜索结果: {results}")
            
            # 清理测试数据
            print("\n=== 清理测试数据 ===")
            task = await index.delete_documents(['test1', 'test2'])
            await client.wait_for_task(task.task_uid)
            print("测试文档已删除")
            
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test()) 