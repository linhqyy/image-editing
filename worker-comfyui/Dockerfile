FROM runpod/worker-comfyui:5.7.1-base

RUN cd /comfyui && git fetch origin && git checkout master && git pull origin master && \
    pip install -r requirements.txt -q

RUN mkdir -p /comfyui/models/diffusion_models \
    /comfyui/models/text_encoders \
    /comfyui/models/vae

RUN wget -q \
    "https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8/resolve/main/flux-2-klein-4b-fp8.safetensors" \
    -O /comfyui/models/diffusion_models/flux-2-klein-4b-fp8.safetensors

RUN wget -q \
    "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors" \
    -O /comfyui/models/text_encoders/qwen_3_4b.safetensors

RUN wget -q \
    "https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors" \
    -O /comfyui/models/vae/flux2-vae.safetensors
