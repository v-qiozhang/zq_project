#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 12/8/2025 上午10:39
# @Author  : v_qiozhang（张琼）
# @FileName: CN_generate_preview_links.py
# @Description :自动获取标记已经更新为是的文档，文章标题和链接连续输出
# 需求拆解与核心步骤
# 网页操作：打开目标页面 → 点击「同步数据」→ 等待同步完成 → 点击「应用发布」→ 处理弹出窗口。
# 数据提取：在弹出的「文章目录变更详情」窗口中，提取指定文章（红框标注）的文章ID和文章标题。
# 链接生成：根据产品ID（从URL或页面提取）和文档ID（文章ID），按格式生成预览链接。
#遗留：
# -通过选择产品，后台调取对应的链接，这样不用手动的粘贴链接
# -点击之后输出预览的链接，一键选中复制
# -在产品确认ok之后，再另外点击一下应用发布，不用再额外打开界面
# -同步的时间，由于不同的产品，量数据不一样，等待的时间不一样，需要给一个选择等待时间的位置，默认20秒，可选项10、60、120
# -在任务详情窗口，可以判断同步完成状态标志作为下一步的一个机制——经过定位，在目录详情位置就会出现，无需再通过状态去定位

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

# 【关键配置】需根据实际网页调整
# TARGET_URL = "https://yehe.woa.com/document/doc-cn/product-article/1424/68331" #数据加速器
TARGET_URL = "https://yehe.woa.com/document/doc-cn/product-article/436/47241" #COS
# TARGET_URL = "https://yehe.woa.com/document/doc-cn/product-article/460/78802" #CI
# TARGET_URL = "https://yehe.woa.com/document/doc-cn/product-article/1105/36355" #HDFS
# 同步数据按钮（定位：类名+子元素文本）
SYNC_BUTTON_XPATH = "//button[contains(@class, 'ant-btn mr8') and .//span='同步数据']"
# 同步结果弹窗（定位：Ant Design弹窗类名+标题文本）
SYNC_MODAL_XPATH = "//div[contains(@class, 'tea-dialog__header') and .//h3[@class='tea-dialog__headertitle' and text()='任务详情']]"
# 同步状态元素的XPath（假设在弹窗内，文本为“成功”，或带有“success”类名）
# SYNC_STATUS_XPATH = "//div[contains(@class, 'ant-tag ant-tag-has-color') and .//span='成功']"
# 刷新目录树按钮（定位：弹窗内文本匹配）
# REFRESH_BUTTON_XPATH = f"{SYNC_MODAL_XPATH}//button[contains(@class, 'ant-btn') and .//span='刷新目录树']"
REFRESH_BUTTON_XPATH = "//button[contains(@class, 'ant-btn') and .//span='刷新目录树']"
# print(REFRESH_BUTTON_XPATH)
# 应用发布按钮（定位：主按钮类名+文本）
PUBLISH_BUTTON_XPATH = "//button[contains(@class, 'ant-btn ant-btn-primary') and .//span='应用发布']"
# 文章变更详情弹窗（定位：弹窗类名+标题文本）
CHANGE_MODAL_XPATH = "//div[contains(@class, 'ant-modal-title') and contains(text(), '文章目录变更详情')]"
# 变更文章表格（定位：表格类名）
# ARTICLE_TABLE_XPATH = f"{CHANGE_MODAL_XPATH}//table[contains(@class, '')]"
# ARTICLE_TABLE_XPATH = ".//div[@role='document'] //tbody[contains(@class, 'ant-table-tbody')]"#未包含外层标题
ARTICLE_TABLE_XPATH = ".//div[@role='document'] //tbody[contains(@class, 'ant-table-tbody')]"
# 产品ID提取关键词（URL中"product-article"后的数字）
FIRST_DATA_ROW_XPATH = "//tbody/tr[1]"  #表格第一行数据（用于等待加载）
PRODUCT_ID_KEYWORD = "product-article"


def extract_product_id(url: str) -> str:
    """从URL中提取产品ID（如"product-article/436/"中的"436"）"""
    parts = url.split("/")
    try:
        # 找到"product-article"的索引，取其后的数字
        idx = parts.index(PRODUCT_ID_KEYWORD)
        return parts[idx + 1]
    except (ValueError, IndexError):
        raise ValueError(f"无法从URL中提取产品ID：{url}")


def run_automation():
    # 初始化Chrome浏览器（需提前安装Chrome驱动）
    global article
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.implicitly_wait(5)  # 全局隐式等待（避免频繁显式等待）

    try:
        # 1. 打开目标页面
        driver.get(TARGET_URL)
        print(f"✅ 成功打开页面：{TARGET_URL}")

        # 2. 点击【同步数据】按钮（等待可点击）
        sync_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, SYNC_BUTTON_XPATH))
        )
        sync_btn.click()
        print("✅ 点击【同步数据】按钮")

        # 3. 等待【同步结果弹窗】出现（Ant Design弹窗需等待"visible"类名）
        sync_modal = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, SYNC_MODAL_XPATH))
        )
        print("✅ 同步结果弹窗已显示")

        # 在弹窗内等待 ** 同步状态变为成功 *
        # WebDriverWait(sync_modal, 20).until(
        #     EC.text_to_be_present_in_element((By.XPATH, SYNC_STATUS_XPATH), "成功")
        # )
        # print("✅ 同步结果完成")

        # 4. 点击【刷新目录树】按钮（在弹窗内定位）
        refresh_btn = WebDriverWait(sync_modal, 10).until(
            EC.element_to_be_clickable((By.XPATH, REFRESH_BUTTON_XPATH))
        )
        refresh_btn.click()
        print("✅ 点击【刷新目录树】按钮")

        # 5. 等待【同步结果弹窗】消失（避免遮挡后续操作）
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((By.XPATH, SYNC_MODAL_XPATH))
        )
        print("✅ 同步结果弹窗消失")

        # 6. 点击【应用发布】按钮（等待可点击）
        publish_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, PUBLISH_BUTTON_XPATH))
        )
        publish_btn.click()
        print("✅ 点击【应用发布】按钮")

        # 7. 等待【文章目录变更详情】弹窗出现
        change_modal = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, CHANGE_MODAL_XPATH))
        )
        print("✅ 文章目录变更详情弹窗出现")
        # print("change_modal结构：\n", change_modal.get_attribute('outerHTML'))  # 这里弹窗只要出现，表格数据其实就已经有了，还有必要去再等待一次吗
        #输出结果：  <div class="ant-modal-title" id="rcDialogTitle0">文章目录变更详情</div>

        table = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, ARTICLE_TABLE_XPATH))
        )
        print("✅ 表格元素已定位")
        # print("table 结构：\n", table.get_attribute('outerHTML'))
        # 输出结果： 应包括所有的表格数据

        # 此时再提取tr（确保元素已存在）
        rows = table.find_elements(By.XPATH, ".//tr") #这里由于已经在table中，无需再从父级别查找

        print(f"rows:{rows}") #通过输出行数，查看有几行数据，这是输出不是具体的多少行，而是具体的行数据
        articles = []
        # print(articles)
        for row in rows:
            cols = row.find_elements(By.XPATH, ".//td")
            # 检查单元格数量（至少包含“内容是否更新”列，即≥5列）
            if len(cols) >= 5:
                # 【关键】第5列（索引4）：内容是否更新（过滤条件）
                content_updated = cols[4].text.strip()
                if content_updated == "是":
                    # 第1列（索引0）：文章ID
                    article_id = cols[0].text.strip()
                    # 第2列（索引1）：文章标题
                    article_title = cols[1].text.strip()
                    # 跳过ID或标题为空的行（避免无效数据）
                    if article_id and article_title:
                        articles.append({"id": article_id, "title": article_title})

        # 验证提取结果
        if not articles:
            raise NoSuchElementException("❌ 未提取到“内容是否更新”为“是”的文章")
        print(f"✅ 提取到{len(articles)}篇“内容更新”的文章")
        # for idx, article in enumerate(articles, 1):
        #     print(f"  第{idx}篇：ID={article['id']}，标题={article['title']}")
        # for 这一段注释了，输出结果如下
        # 第1篇：ID = 77960，标题 = 客户端的规格与限制
        # 第2篇：ID = 77950，标题 = 快速入门
        # 第3篇：ID = 118372，标题 = 管理GooseFSx超级目录和目录配额


        # 9. 生成【预览链接】（格式：product_id/article_id）
        product_id = extract_product_id(TARGET_URL)
        preview_links = []
        for article in articles:
            link = f"https://tcloud.woa.com/document/product/{product_id}/{article['id']}?!preview"
            preview_links.append({
                "title": article["title"],
                "id": article["id"],
                "preview_link": link
            })

        # # 10. 输出结果（可选：保存到CSV/数据库）：按标题、id、链接 连续展示
        # print("\n📊 预览链接生成结果：")
        # for link_info in preview_links:
        #     print(f"标题：{link_info['title']}")
        #     # print(f"文章ID：{link_info['id']}")
        #     print(f"预览链接：{link_info['preview_link']}")
        #     print("-" * 50)

        # 10.输出标题列表（连续展示）
        # print("\n" + "=" * 50)
        # 1. 定义分隔线（与用户示例一致）
        SEPARATOR = "-" * 50  # 生成50个短横线，匹配用户示例中的分隔线

        # 2. 提取标题列表（从preview_links中取出所有title）
        titles = [item["title"] for item in preview_links]

        # 3. 提取预览链接列表（从preview_links中取出所有preview_link）
        links = [item["preview_link"] for item in preview_links]

        # 4. 输出标题列表（带序号、符合用户格式）
        if titles:  # 仅当有标题时输出
            print("📌 符合条件的文章标题列表：")
            for idx, title in enumerate(titles, 1):  # 从1开始计数
                print(f"{idx}. {title}")
            print(f"\n{SEPARATOR}\n")  # 标题列表后添加分隔线（带换行）
        else:
            print("❌ 未找到符合条件的文章标题")

        # 5. 输出预览链接列表（带序号、符合用户格式）
        if links:  # 仅当有链接时输出
            print("🔗 符合条件的文章预览链接列表：")
            for idx, link in enumerate(links, 1):  # 从1开始计数
                # print(f"{idx}. {link}") #输出有数字，不好批量打开
                print(f"{link}")
        else:
            print("❌ 未找到符合条件的预览链接")

    except TimeoutException as e:
        # print(f"❌ 操作超时：{str(e)}（请检查网络或元素等待条件）")
        print(f"❌ 操作超时：（请检查网络或元素等待条件）")
    except NoSuchElementException as e:
        print(f"❌ 元素未找到：{str(e)}（请检查XPath是否正确）")
    except ValueError as e:
        print(f"❌ 数据提取失败：{str(e)}")
    except Exception as e:
        print(f"❌ 自动化流程失败：{str(e)}")
    finally:
        # 关闭浏览器（无论成功与否）
        driver.quit()
        print("\n🔒 浏览器已关闭")


if __name__ == "__main__":
    run_automation()
