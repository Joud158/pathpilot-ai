import gradio as gr
from agent_core import respond

CSS = """.gradio-container {max-width: 1000px !important; margin: auto !important;} .hero {text-align:center;padding:20px 0 6px;} .hero h1 {font-size:2.4rem;letter-spacing:-.05em;color:#176d54;} .hero p {color:#6b7280;} footer {display:none !important;}"""
with gr.Blocks(title="PathPilot AI | Career Concierge", css=CSS, theme=gr.themes.Soft(primary_hue="green", neutral_hue="slate")) as demo:
    gr.HTML('<div class="hero"><h1>PathPilot AI</h1><p>Career guidance, made personal. Meet Nova, your virtual concierge.</p></div>')
    gr.ChatInterface(fn=respond, type="messages", chatbot=gr.Chatbot(height=490, type="messages", show_label=False),
        textbox=gr.Textbox(placeholder="Ask about coaching, prices, or getting started...", container=False, scale=8),
        examples=["What services and prices do you offer?", "I'm interested in a mock interview.", "My name is Alex Lee and my email is alex@example.com. Please contact me about a mock interview.", "Do you offer refunds?", "I have feedback: please add weekend appointments."],
        cache_examples=False)
    gr.Markdown("*Demo business only. Do not share sensitive information. This assistant logs customer interest and feedback locally; it does not send emails or take payments.*")
if __name__ == "__main__":
    demo.launch()
