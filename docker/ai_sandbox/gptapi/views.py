from django.shortcuts import render

from openai import OpenAI
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class chatgpt(APIView):
    def post(self, request):
        code = request.data.get("Code", "").strip()
        history = request.session.get("grading_history", [])
        print("Session key:", request.session.session_key)
        print("History:", request.session.get("grading_history"))

        if code:

            # 添加本轮输入到上下文历史
            history.append({"role": "user", "content": code})

            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=history,
                    temperature=0.5, # 更理性
                    max_tokens=1000
                )
                reply = response.choices[0].message.content.strip()

                # 保存回复到历史
                history.append({"role": "assistant", "content": reply})
                request.session["grading_history"] = history
                request.session.modified = True

                return Response({"response": reply})
            except Exception as e:
                return Response({"error": str(e)}, status=500)
            
        else:
            statement = request.data.get("Statement", "").strip()
            sample = request.data.get("Sample", "").strip()
            sample_explanation = request.data.get("SampleExplanation", "").strip()
            style_criteria = request.data.get("StyleCriteria", "").strip()
            implement_criteria = request.data.get("ImplementCriteria", "").strip()
            possible = request.data.get("Possible", "").strip()

            # 检查 Statement 是否为空（必填项）
            if not statement:
                return Response({"error": "字段 Statement（题目描述）不能为空。"}, status=400)
            
            # 构建 system_content
            system_content = "假如你是一名经验丰富的大学计算机教授，下面是一道课后作业，学生需要阅读以下题面严格按照其中的输入、输出格式编写结构清晰、可读性高的代码，使之在尽可能优秀的时间与空间实现下完成题面要求：" + "\n"
            system_content += statement + "\n"

            if sample:
                system_content += "下面我将给出示例代码：" + "\n"
                system_content += sample + "\n"
            
            if sample_explanation:
                system_content += "这是示例代码具体实现的解释：" + "\n"
                system_content += sample_explanation + "\n"
            
            system_content += "下面我将给出很多学生的作业，请你完成以下任务：" + "\n"
            system_content += "1.就学生作业的代码风格进行评分，以示例代码为模板，满分为100分。" + "\n"

            if style_criteria:
                system_content += "下面是代码风格的具体要求：" + "\n"
                system_content += style_criteria + "\n"
            
            system_content += "2.就学生作业的代码实现进行评分，以示例代码的具体实现为模板，满分为100分。" + "\n"

            if implement_criteria:
                system_content += "下面是代码实现的具体要求：" + "\n"
                system_content += implement_criteria + "\n"
            
            if possible:
                system_content += "下面我将给出一些可能的实现以及分值：" + "\n"
                system_content += possible + "\n"
            
            system_content += "3. 就代码风格、代码实现两方面给出简短的评价和详细的的修改意见。" + "\n"
            system_content += "在输出时，请不要输出其他内容，仅按照我下面给出的格式输出三行内容：" + "\n"
            system_content += "S: 代码风格评分" + "\n"
            system_content += "I: 代码实现评分" + "\n"
            system_content += "N: 简短的评价和详细的的修改意见" + "\n"
            system_content += "如果收到的请求不是代码，请不要输出其他内容，只输出一个字符E表示错误" + "\n"
            
            # 构建系统提示信息
            if "grading_history" not in request.session:
                request.session["grading_history"] = [
                    {
                        "role": "system",
                        "content": system_content
                    }
                ]

            history = request.session["grading_history"]

            return Response({"response": system_content})
