# PaperPuller Interest Profile

I am interested in papers that can help improve Ship License Plate Recognition (SLPR), a specialized scene text recognition task with Chinese characters, digits, English/Pinyin text, complex layouts, and severe real-world visual degradation.

Prioritize papers that address one or more of these SLPR challenges:

1. Robust text recognition under degradation:
   blur, motion blur, low light, back light, over-exposure, rain/fog, noise, compression artifacts, occlusion, incomplete characters, and surveillance-like imaging.

2. Complex layout recognition:
   multi-line text, vertical text, irregular layout, discontinuous text, long text sequences, non-standard reading order, and layout-aware recognition.

3. Mixed-script and structured recognition:
   Chinese OCR, multilingual OCR, mixed Chinese-English-digit recognition, license plate recognition, domain-specific character constraints, and visually similar character disambiguation.

4. Stronger visual representation for OCR/STR:
   improved visual encoders, Vision Transformer variants, robust backbones, self-supervised learning, masked autoencoder, masked image modeling, masked visual modeling, OCR-aware pretraining, and representation learning for text images.

5. Semantic or language-aware enhancement:
   vision-language alignment, contrastive learning, text-image feature alignment, semantic consistency, language-guided recognition, context-aware decoding, and visual-semantic representation learning.

6. Degradation-aware data and adaptation:
   OCR/STR data augmentation, synthetic text images, degradation simulation, domain adaptation, domain generalization, image restoration, enhancement, deblurring, low-light enhancement, and text image super-resolution when evaluated by recognition accuracy.

7. Error correction and decision-level improvement:
   confidence calibration, uncertainty estimation, reranking, ensemble or committee methods, character confusion analysis, hard-sample mining, replacement-error correction, and sequence-level refinement.

Prefer papers with clear methods, reproducible experiments, released code, useful ablations, hard/degraded/irregular/multilingual case analysis, or a plausible path to integration into an encoder-decoder STR pipeline.

Down-rank papers mainly about pure LLM prompting, document QA without recognition improvement, text detection only, generic image generation/restoration without OCR evaluation, medical imaging, robotics, 3D reconstruction, remote sensing without text recognition, or general ML without a clear OCR/STR connection.
