import os
import smtplib
from email.header import Header
from email.mime.text import MIMEText
import streamlit as st
from openai import OpenAI

# -------------------------------------------------------------------------
# 頁面基本設定與自訂主題色彩 (#cd9e97 奶油色調)
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="紅斗泥人才招募系統", page_icon="🍡", layout="centered"
)

# 套用專屬色系與美化 CSS
st.markdown(
    """
    <style>
    /* 整體背景與主色調 */
    .stApp {
        background-color: #fcf9f8;
    }
    /* 按鈕樣式自訂 */
    .stButton>button {
        background-color: #e0c4bc;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #cda89e;
        color: #ffffff;
    }
    /* 標題與文字微調 */
    h1, h2, h3 {
        color: #5c4033;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 優先從 Streamlit Secrets 讀取，若無則抓取環境變數
api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
client = OpenAI(api_key=api_key)

# 初始化 Session State 用於頁面跳轉與資料暫存
if "page" not in st.session_state:
  st.session_state.page = 1
if "random_questions" not in st.session_state:
  st.session_state.random_questions = []
if "final_summary" not in st.session_state:
  st.session_state.final_summary = ""

# -------------------------------------------------------------------------
# 核心提示詞與 AI 函式
# -------------------------------------------------------------------------
JOB_CONTEXT = """
【店舖與工作情境背景】
1. 核心產品：手工大福製作，內場需要極度細心、手巧、動作俐落。
2. 內場特性：工作具高度重複性，長時間站立，同一崗位需長時間專注，不能怕無聊。
3. 前台特性：若資質優秀需支援前台。前台為店內中樞神經，需具備極佳的抗干擾能力、多工切換速度、清晰邏輯與親切服務態度。
4. 複雜作業環境：
   - 訂單來源多元：官網、Uber Eats、LINE 客服、現場購買。
   - 現場客群分流：取貨客（需快速核對拿取）與現場購買客。
   - 前台必須即時將各平台訂單資訊交接給內場，並處理現場介紹、包裝、結帳。
   - 金流與結帳：支援 LINE Pay、現金、信用卡三種方式，結帳與現金點收必須零失誤。
   - 雜務協調：無客人時需處理客戶滿意度調查表與折紙盒等手工雜務。
"""


def generate_random_questions():
  """強制每次呼叫 API 生成 5 個隨機情境題"""
  prompt = f"""
{JOB_CONTEXT}

請根據這些工作性質隨機發送五個測試面試者的情境狀況題目給我。
每次產生的題目角度與語境都必須盡量不同。
題目不可太長，約 15~25 字。
嚴格依照以下格式回傳，並且不得有多餘文字：
題目1：...
題目2：...
題目3：...
題目4：...
題目5：...
"""
  response = client.chat.completions.create(
      model="gpt-4o",
      messages=[{"role": "user", "content": prompt}],
      temperature=0.9,
  )
  text = response.choices[0].message.content.strip()
  lines = [line.strip() for line in text.split("\n") if line.strip()]
  return lines[:5]


def analyze_candidate_data(data):
  """分析求職者回答並產出結構化報告"""
  prompt = f"""
你是一位紅斗泥甜點業招募官與店長教練。請協助我分析以下求職者的面試問答內容，判斷其是否適合我們店舖的工作職位。【店舖與工作情境背景】請以符合我們店舖文化背景的標準評比（類網美店 6入大福售價約在320~360台幣 並注重質感與少女感的甜點店 ） 
1. 核心產品：手工大福製作，內場需要極度細心、手巧、動作俐落。
2. 內場特性：工作具高度重複性，長時間站立，同一崗位需長時間專注，不能怕無聊。
3. 前台特性：若資質優秀需支援前台。前台為店內中樞神經，需具備極佳的抗干擾能力、多工切換速度、清晰邏輯與親切服務態度。
4. 複雜作業環境：
   - 訂單來源多元：官網、Uber Eats、LINE 客服、現場購買。
   - 現場客群分流：取貨客（需快速核對拿取）與現場購買客。
   - 前台必須即時將各平台訂單資訊交接給內場，並處理現場介紹、包裝、結帳。
   - 金流與結帳：支援 LINE Pay、現金、信用卡三種方式，結帳與現金點收必須零失誤。
   - 雜務協調：無客人時需處理客戶滿意度調查表與折紙盒等手工雜務。。

{JOB_CONTEXT}

【求職者填答資料】
{data}

【分析任務與輸出格式】
請根據求職者的填答內容，輸出以下結構化報告：
1. 適性評分：給出整體綜合評分（0~100分），並詳述評分理由。
2. 職位適配性判斷：
   - 適合內場（手藝耐勞組）：評估其抗無聊、專注力與穩定度。
   - 適合前台（多工應變組）：評估其抗壓性、多工處理與細心度（特別是金流與訂單交接）。
3. 潛在優點：根據求職者的基本資料、作答風格與答案中找出可能發揮的淺在優點 
4. 潛在隱憂（Red Flags）：指出求職者回答中透露的可能風險。
5. 錄用建議與複試追問：給出最終錄用建議，並提供 2-3 個若進入現場面試時需要特別抽問的追話題目。
"""
  response = client.chat.completions.create(
      model="gpt-4o",
      messages=[{"role": "user", "content": prompt}],
      temperature=0.3,
  )
  return response.choices[0].message.content.strip()


def send_emails_to_managers(candidate_name, content):
  """自動發送 AI 分析報告，一次寄出三封信（可發給不同人或同一人三個備份）"""
  sender_email = st.secrets.get("EMAIL_USER", "")
  sender_password = st.secrets.get("EMAIL_PASSWORD", "")

  # 從 Secrets 讀取三個收件人信箱（支援 manager1, manager2, manager3）
  receivers = [
      st.secrets.get("MANAGER_EMAIL_1", sender_email),
      st.secrets.get("MANAGER_EMAIL_2", sender_email),
      st.secrets.get("MANAGER_EMAIL_3", sender_email),
  ]

  if not sender_email or not sender_password:
    return False

  success_count = 0
  try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
      server.login(sender_email, sender_password)

      # 迴圈發送三封信
      for receiver in receivers:
        if not receiver:
          continue
        message = MIMEText(content, "plain", "utf-8")
        message["From"] = Header(f"紅斗泥招募系統 <{sender_email}>", "utf-8")
        message["To"] = Header(receiver, "utf-8")
        message["Subject"] = Header(
            f"【新應徵通知】{candidate_name} 的面試分析報告", "utf-8"
        )

        server.sendmail(sender_email, [receiver], message.as_string())
        success_count += 1

    return success_count > 0
  except Exception as e:
    print(f"自動寄信失敗：{e}")
    return False


# -------------------------------------------------------------------------
# 頁面一：首頁
# -------------------------------------------------------------------------
if st.session_state.page == 1:
  st.title("🍡 紅斗泥人才招募系統")
  st.write("歡迎來到紅斗泥！請點擊下方按鈕開始填寫應徵問卷。")

  if st.button("點擊開始應徵", type="primary", use_container_width=True):
    with st.spinner("正在透過 AI 為您動態生成專屬測驗題組..."):
      try:
        st.session_state.random_questions = generate_random_questions()
        st.session_state.page = 2
        st.rerun()
      except Exception as e:
        st.error(
            f"⚠️ API 動態抽題失敗！請檢查 Streamlit Secrets 的 OPENAI_API_KEY"
            f" 是否正確。錯誤訊息：{e}"
        )

# -------------------------------------------------------------------------
# 頁面二：填寫與測驗頁
# -------------------------------------------------------------------------
elif st.session_state.page == 2:
  st.title("🍡 紅斗泥 - 應徵者問卷")

  with st.form("application_form"):
    st.subheader("第一階段：基本資料")
    name = st.text_input("姓名")
    gender = st.selectbox("性別", ["請選擇", "男", "女", "多元性別/不願透露"])

    st.write("出生日期")
    col_y, col_m, col_d = st.columns(3)
    with col_y:
      birth_year = st.selectbox(
          "年份", options=[str(y) for y in range(2026, 1945, -1)], index=28
      )
    with col_m:
      birth_month = st.selectbox(
          "月份", options=[f"{m:02d}" for m in range(1, 13)]
      )
    with col_d:
      birth_day = st.selectbox("日期", options=[f"{d:02d}" for d in range(1, 32)])
    birth_date = f"{birth_year}/{birth_month}/{birth_day}"

    mbti = st.selectbox(
        "你的 MBTI",
        [
            "未測試過",
            "INTJ",
            "INTP",
            "ENTJ",
            "ENTP",
            "INFJ",
            "INFP",
            "ENFJ",
            "ENFP",
            "ISTJ",
            "ISFJ",
            "ESTJ",
            "ESFJ",
            "ISTP",
            "ISFP",
            "ESTP",
            "ESFP",
        ],
    )
    highest_edu = st.selectbox(
        "最高學歷", ["高中職", "專科", "大學", "碩士以上", "其他"]
    )
    is_student = st.radio("是否在學中", ["否", "是"], horizontal=True)
    marital_status = st.radio("婚姻狀況", ["未婚", "已婚"], horizontal=True)
    address = st.text_input("住址（鄉鎮市區即可）")
    commute_time = st.selectbox(
        "通勤時間",
        [
            "10分鐘內",
            "10~20分鐘",
            "20~35分鐘",
            "35~50分鐘",
            "大於50分鐘",
        ],
    )
    role_priority = st.radio(
        "崗位優先順序", ["內場 > 外場", "外場 > 內場", "皆可"], horizontal=True
    )
    phone = st.text_input("聯絡電話")

    st.markdown("---")
    st.subheader("第二階段：工作經歷與動機")
    q1 = st.selectbox(
        "Q1. 上一份工作是否超過半年？",
        [
            "無工作經驗",
            "少於半年",
            "半年～一年",
            "一年～兩年",
            "兩年以上",
        ],
    )
    q2 = st.text_input("Q2. 上份工作為：職務＆公司？")
    q3 = st.text_area("Q3. 上份工作為什麼離職？")
    q4 = st.text_area("Q4. 為什麼想來紅斗泥上班？")
    q5 = st.text_area(
        "Q5. 你平時休閒時喜歡做什麼呢？興趣、嗜好？（不限字數，請盡可能介紹自己）"
    )

    st.markdown("---")
    st.info(
        "💡 **【工作環境與狀況說明】**\n\n"
        "我們是一間重視手藝與細節的手作大福品牌。內場工作具有高度重複性、需要長時間站立與高度專注；"
        "前台則是店內中樞神經，需面對多元訂單來源（官網、Uber Eats、LINE、現場）、處理現金與電子支付金流，"
        "並在空檔主動協助折紙盒與滿意度調查表。了解並認同這樣的工作節奏，是我們非常看重的特質！"
    )

    st.markdown("---")
    st.subheader("第三階段：情境題作答")
    st.write("請根據以下 5 個由 AI 動態生成的隨機情境回答您的想法：")

    if not st.session_state.random_questions:
      st.warning("請先從首頁點擊「點擊開始應徵」以產生題目！")
      st.stop()

    q_answers = []
    for idx, q in enumerate(st.session_state.random_questions):
      ans = st.text_area(f"{q}", key=f"q_ans_{idx}")
      q_answers.append(f"{q}\n回答：{ans}")

    submitted = st.form_submit_button("確認送出問卷", type="primary")

    if submitted:
      if not name or not phone:
        st.error("請至少填寫「姓名」與「聯絡電話」才能送出喔！")
      else:
        formatted_data = f"""
【基本資料】
- 姓名: {name}
- 性別: {gender}
- 出生日期: {birth_date}
- MBTI: {mbti}
- 最高學歷: {highest_edu}
- 是否在學中: {is_student}
- 婚姻狀況: {marital_status}
- 住址: {address}
- 通勤時間: {commute_time}
- 崗位優先順序: {role_priority}
- 聯絡電話: {phone}

【經歷與動機】
- Q1工作年資: {q1}
- Q2上份工作: {q2}
- Q3離職原因: {q3}
- Q4應徵動機: {q4}
- Q5自我介紹與興趣: {q5}

【情境題回答】
{'\n\n'.join(q_answers)}
"""
        with st.spinner(
            "記錄中，請稍候..."
        ):
          analysis_result = analyze_candidate_data(formatted_data)

          final_report = f"""【求職者面試摘要報告】
{formatted_data}

====================
{analysis_result}"""

          # 自動發送三封信
          email_sent = send_emails_to_managers(name, final_report)

        if email_sent:
          st.success("✅ AI 分析完成，已同步自動發送三封通知信給相關人員！")
        else:
          st.info("ℹ️ AI 分析完成！")

        st.session_state.final_summary = final_report
        st.session_state.page = 3
        st.rerun()

# -------------------------------------------------------------------------
# 頁面三：整理與複製頁
# -------------------------------------------------------------------------
elif st.session_state.page == 3:
  st.title("🎉 問卷已成功送出！")
  st.write("感謝您的填答，我們已收到您的資訊。")

  st.markdown("---")
  st.subheader("📋 店長專用：AI 分析與整理內容")
  st.write("（點擊下方文字框右上角即可快速複製）")

  summary_text = st.session_state.get("final_summary", "無資料")
  st.text_area("分析結果總覽", summary_text, height=400)

  st.markdown(
      "👇 **請將本訊息複製貼到ＩＧ或ＦＢ對話中**",
      unsafe_allow_html=True,
  )

  col1, col2 = st.columns(2)
  with col1:
    if st.button("🔄 重新填寫另一份", use_container_width=True):
      st.session_state.page = 1
      st.session_state.final_summary = ""
      st.session_state.random_questions = []
      st.rerun()
