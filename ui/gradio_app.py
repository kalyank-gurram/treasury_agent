import gradio as gr
import httpx
import os

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def ask(question, entity):
    with httpx.Client(timeout=60) as c:
        r = c.post(f"{BACKEND}/chat", json={"question": question, "entity": entity or None})
        r.raise_for_status()
        data = r.json()
    return f"Intent: {data['intent']}\nNotes: {data.get('notes','')}\n\nResult:\n{data['result']}"

with gr.Blocks() as demo:
    gr.Markdown("# Treasury Agent (Demo UI)")
    with gr.Row():
        entity = gr.Textbox(label="Entity (optional, e.g., ENT-01)")
    with gr.Row():
        q = gr.Textbox(label="Ask", value="What are my current account balances?")
    out = gr.Textbox(label="Response", lines=20)
    btn = gr.Button("Run")
    btn.click(ask, inputs=[q, entity], outputs=out)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)