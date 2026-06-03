# Research Interest Profile

<!-- Copy this file to config/interest.md and customize it for your research area.
     All sections except the free-form description at the top are optional.
     Use config/CHATGPT_PROMPT.md to have an AI assistant generate this file for you. -->

I am interested in papers that can help improve Ship License Plate Recognition (SLPR), a specialized scene text recognition task with Chinese characters, digits, English/Pinyin text, complex layouts, and severe real-world visual degradation.

## Evaluation Criteria

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

## Groups

- Must Read: high-score papers with code and direct applicability
- Robust Recognition / Degradation: papers addressing degradation, occlusion, domain shift
- Complex Layout / Structured Recognition: multi-line, vertical, mixed-script, long sequences
- Visual Encoder / Pretraining: ViT, MAE, self-supervised visual learning
- Semantic Enhancement / Decoder: vision-language alignment, context-aware decoding
- Data / Augmentation / Restoration: data augmentation, synthetic data, image restoration
- Reranking / Error Correction: confidence calibration, error correction, ensemble methods
- Related Work / Others: everything else

## Local Keywords

- OCR: ocr, optical character recognition, document understanding, text spotting
- STR: scene text, text recognition, text detection, text recognizer
- ViT: vision transformer, vit, transformer-based vision, visual transformer
- MAE: masked autoencoder, mae, masked image modeling, self-supervised visual
- Augmentation: augmentation, synthetic data, domain randomization, data synthesis

## Extra Fields

Please also return these additional fields in the `extra` JSON object:
- challenges: array of challenge types addressed (degradation, occlusion, complex_layout, multi_line, vertical_text, long_sequence, mixed_script, domain_shift)
- pipeline_components: array of pipeline components (visual_encoder, mae_pretraining, semantic_enhancement, decoder, data_augmentation, restoration, domain_adaptation, reranking, error_correction, benchmark_or_dataset, analysis_only)
- reproducibility: one of "high", "medium", "low", "unknown"
