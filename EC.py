import os
import pandas as pd
from openpyxl import load_workbook
from PIL import Image as PILImage
import io
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from config import source_path
from utils import load_from_dataset


class DataSet:
    def __init__(self, folder, output_excel="Dataset.csv", output_images_dir="images"):
        self.folder = folder
        self.output_excel = output_excel
        self.output_images_dir = output_images_dir
        if os.path.exists(output_excel):
            self.dataset = load_from_dataset(input_excel=output_excel, images_dir=output_images_dir)
        else:
            self.dataset = self.main(folder)

    def identify_template(self, sheet):
        """识别模板类型"""
        a1_value = sheet['A1'].value
        if a1_value and 'STG Customer' in str(a1_value):
            return 'STG'
        elif a1_value and ('CML Customer' in str(a1_value) or "CML Customer's Name" in str(a1_value) or "Customer's Name" in str(a1_value)):
            return 'CML'
        else:
            return 'Unknown'

    def read_stg_template(self, sheet):
        """读取STG模板的指定内容"""
        base_info = {
            'Customer Name': sheet['C1'].value,
            'Customer P/N': sheet['C2'].value,
            'Factory P/N': sheet['E2'].value,
            'Date': sheet['E3'].value,
            'Base Material': sheet['C7'].value,
            'Solder Mask': sheet['E7'].value,
            'Via Plugging Type': sheet['C10'].value,
            'STG P/N': sheet['C3'].value,
            'Engineer': sheet['E1'].value,
            "Panel Size": sheet['E8'].value,
        }
        
        issues = []
        row = 13
        while sheet[f'A{row}'].value:
            if sheet[f'B{row}'].value is None:
                row += 1
                continue
            issue = {
                'No': sheet[f'A{row}'].value,
                'Description': {'text': sheet[f'B{row}'].value, 'image': []},
                'Factory Suggestion': {'text': sheet[f'C{row}'].value, 'image': []},
                'STG Proposal': {'text': sheet[f'D{row}'].value, 'image': []},
                'Customer Decision': {'text': sheet[f'E{row}'].value, 'image': []},
                'EQ Status': sheet[f'F{row}'].value
            }
            issue.update(base_info)
            issues.append(issue)
            row += 1
        return issues

    def read_cml_template(self, sheet):
        """读取CML模板的指定内容"""
        base_info = {
            'Customer Name': sheet['C1'].value,
            'Customer P/N': sheet['C2'].value,
            'Factory P/N': sheet['E2'].value,
            'Date': sheet['E3'].value,
            'Base Material': sheet['C7'].value,
            'Solder Mask': sheet['E7'].value,
            'Via Plugging Type': None,
            "STG P/N": sheet['C3'].value,
            "Engineer": sheet['E1'].value,
            'Panel Size': None
        }
        
        issues = []
        row = 10
        while sheet[f'A{row}'].value:
            if sheet[f'B{row}'].value is None:
                row += 1
                continue
            issue = {
                'No': sheet[f'A{row}'].value,
                'Description': {'text': sheet[f'B{row}'].value, 'image': []},
                'Factory Suggestion': {'text': sheet[f'C{row}'].value, 'image': []},
                'STG Proposal': {'text': None, 'image': []},
                'Customer Decision': {'text': sheet[f'D{row}'].value, 'image': []},
                'EQ Status': sheet[f'E{row}'].value
            }
            issue.update(base_info)
            issues.append(issue)
            row += 1
        return issues

    def extract_images(self, sheet, output_dir, file_name):
        """提取Excel中的图片并按行存储，保存到本地并记录文件名"""
        images = {}
        idx = 0
        for img in sheet._images:
            anchor = img.anchor
            row = anchor._from.row
            col = anchor._from.col
            images[row] = images.get(row, [])
            try:
                img_data = img._data()
                pil_img = PILImage.open(io.BytesIO(img_data))
                img_filename = f"{file_name}_image_{idx + 1}.png"
                output_path = os.path.join(output_dir, img_filename)
                pil_img.save(output_path)
                images[row].append(img_filename)
                idx += 1
            except AttributeError:
                print(f"无法提取图片 {idx + 1} 的数据")
        return images

    def process_excel(self, file_path, output_dir):
        """主函数：处理Excel文件"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        wb = load_workbook(file_path)
        sheet = wb.active
        
        template_type = self.identify_template(sheet)
        
        if template_type == 'STG':
            issues = self.read_stg_template(sheet)
        elif template_type == 'CML':
            issues = self.read_cml_template(sheet)
        else:
            print(file_path)
            raise ValueError("Unknown template type")
        
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        images = self.extract_images(sheet, output_dir, file_name)

        for issue in issues:
            if str(issue['No']).isdigit():
                row_num = int(issue['No']) + 12 if template_type == 'STG' else int(issue['No']) + 9
                if row_num in images:
                    for field in ['Description', 'Factory Suggestion', 'STG Proposal', 'Customer Decision']:
                        if field in issue:
                            issue[field]['image'] = images[row_num]
            issue['FileName'] = os.path.basename(file_path)

        return issues, template_type

    def save_to_excel(self, dataset, output_excel):
        """将数据集保存为 Excel 文件"""
        flat_data = []
        count = 0
        for issue in dataset:
            flat_issue = {
                "Index": count,
                'No': issue['No'],
                'Description': issue['Description']['text'],
                'Description_Images': ';'.join(issue['Description']['image']),
                'Factory Suggestion': issue['Factory Suggestion']['text'],
                'Factory_Suggestion_Images': ';'.join(issue['Factory Suggestion']['image']),
                'STG Proposal': issue['STG Proposal']['text'],
                'STG_Proposal_Images': ';'.join(issue['STG Proposal']['image']),
                'Customer Decision': issue['Customer Decision']['text'],
                'Customer_Decision_Images': ';'.join(issue['Customer Decision']['image']),
                'EQ Status': 'Closed',
                'Customer Name': issue['Customer Name'],
                'Customer P/N': issue['Customer P/N'],
                'Factory P/N': issue['Factory P/N'],
                'Date': issue['Date'],
                'Base Material': issue['Base Material'],
                'Solder Mask': issue['Solder Mask'],
                'Via Plugging Type': issue['Via Plugging Type'],
                'Engineer Name': issue['Engineer'],
                'Panel Size': issue['Panel Size'],
                'STG P/N': issue['STG P/N'],
                'FileName': issue['FileName'],
                'Previous Case': True,
                "Closed Date": '2025-01-01'
            }
            flat_data.append(flat_issue)
            count += 1
        
        df = pd.DataFrame(flat_data)
        df.to_csv(output_excel, index=False)
        print(f"数据集已保存到 {output_excel}")

    def main(self, folder):
        """生成数据集并保存为 Excel"""
        global missed
        dataset = []
        files = list(os.walk(folder))[0][2]
        missed = []
        for i in files:
            try:
                if i.endswith('.xlsx'):
                    issues, template = self.process_excel(os.path.join(folder, i), self.output_images_dir)
                    dataset.extend(issues)
                else:
                    missed.append(i)
            except:
                missed.append(i)
            
        if dataset:
            self.save_to_excel(dataset, self.output_excel)
        return dataset
        
    def update(self, folder):
        """更新数据集"""
        self.dataset = self.main(folder)
        return self.dataset

class Engine:
    def __init__(self, dataset=None, vectorstore_path="Model", output_excel="Dataset.csv", output_images_dir="images"):
        self.vectorstore_path = vectorstore_path
        self.output_excel = output_excel
        self.output_images_dir = output_images_dir
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        
        # 如果本地存在向量模型，直接加载
        if os.path.exists(vectorstore_path):
            print(f"从 {vectorstore_path} 加载现有向量模型")
            self.vectorstore = FAISS.load_local(vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)
            # 加载数据集
            print(f"从 {output_excel} 加载数据集")
            self.dataset = load_from_dataset(input_excel=output_excel, images_dir=output_images_dir)
            
        else:
            # 如果没有本地模型，必须提供 dataset
            if dataset is None:
                raise ValueError("未提供数据集且本地不存在向量模型")
            print("构建新的向量模型")
            self.dataset = dataset
            self.vectorstore = self.build_vectorstore(dataset)
            self.vectorstore.save_local(vectorstore_path)
            print(f"向量模型已保存到 {vectorstore_path}")

    def build_vectorstore(self, dataset):
        """从数据集中构建 FAISS 向量存储"""
        if not dataset:
            raise ValueError("数据集为空")
        texts = [issue['Description']['text'] for issue in dataset]
        documents = [Document(page_content=text, metadata=issue) for text, issue in zip(texts, dataset)]
        vectorstore = FAISS.from_documents(documents, self.embeddings, distance_strategy="COSINE")
        return vectorstore

    def search_similar_descriptions(self, query, customer_name=None, k=20):
        """搜索与查询描述最相似的前 k 个问题记录，可按客户名称过滤"""
        if not query:
            return []
        
        docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=len(self.dataset))
        
        results = []
        for doc, score in docs_and_scores:
            issue = doc.metadata
            if customer_name is None or issue['Customer Name'].lower() == customer_name.lower():
                issue['similarity_score'] = score
                results.append(issue)
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        if not results and customer_name:
            print(f"未找到客户 '{customer_name}' 的匹配记录")
        return results[:k]

    def print_similar_issues(self, similar_issues):
        """打印相似问题记录的详细信息"""
        for idx, issue in enumerate(similar_issues, 1):
            print(f"排名 {idx}: 相似度分数 = {issue['similarity_score']:.4f}")
            print(f"  文件: {issue['FileName']}")
            print(f"  问题编号: {issue['No']}")
            print(f"  描述: {issue['Description']['text']}")
            print(f"  描述图片: {'; '.join(issue['Description']['image']) if issue['Description']['image'] else '无'}")
            print(f"  工厂建议: {issue['Factory Suggestion']['text'] if issue['Factory Suggestion']['text'] is not None else '无'}")
            print(f"  工厂建议图片: {'; '.join(issue['Factory Suggestion']['image']) if issue['Factory Suggestion']['image'] else '无'}")
            print(f"  STG 提案: {issue['STG Proposal']['text'] if issue['STG Proposal']['text'] is not None else '无'}")
            print(f"  STG 提案图片: {'; '.join(issue['STG Proposal']['image']) if issue['STG Proposal']['image'] else '无'}")
            print(f"  客户决定: {issue['Customer Decision']['text'] if issue['Customer Decision']['text'] is not None else '无'}")
            print(f"  客户决定图片: {'; '.join(issue['Customer Decision']['image']) if issue['Customer Decision']['image'] else '无'}")
            print(f"  EQ 状态: {issue['EQ Status']}")
            print(f"  客户名称: {issue['Customer Name']}")
            print(f"  客户零件号: {issue['Customer P/N']}")
            print(f"  工厂零件号: {issue['Factory P/N']}")
            print(f"  日期: {issue['Date']}")
            print(f"  基材: {issue['Base Material'] if issue['Base Material'] is not None else '无'}")
            print(f"  阻焊层: {issue['Solder Mask'] if issue['Solder Mask'] is not None else '无'}")
            print(f"  过孔填充类型: {issue['Via Plugging Type'] if issue['Via Plugging Type'] is not None else '无'}")
            print("-" * 50)

# 示例用法
if __name__ == "__main__":
    if not os.path.exists("faiss_index/index.faiss"):
        # 场景 1：初次运行，生成数据集和向量模型
        print("场景 1：初次运行，生成数据集和向量模型")
        cleaner = DataSet('Data/EQ Excel', output_excel="Data/Dataset.csv", output_images_dir="Data/images")
        dataset = cleaner.dataset

        core = Engine(dataset=dataset, vectorstore_path="Data/Model", output_excel="Data/Dataset.csv", output_images_dir="Data/images")
        query = "电路短路问题"
        customer_name = "Huf"
        similar_issues = core.search_similar_descriptions(query, customer_name=customer_name, k=20)
        core.print_similar_issues(similar_issues)
    else:
        # 场景 2：本地存在模型，直接加载
        print("\n场景 2：本地存在模型，直接加载")
        core = Engine(vectorstore_path="faiss_index", output_excel="Data/Dataset.csv", output_images_dir="Data/images")
        query = "电路短路问题"
        customer_name = "Huf"
        similar_issues = core.search_similar_descriptions(query, customer_name=customer_name, k=20)
        core.print_similar_issues(similar_issues)
        