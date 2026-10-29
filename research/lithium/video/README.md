# How the explainer video is made

1. `narration.py` holds the script, scene by scene.
2. `tts.py` voices it with the open-source Kokoro text-to-speech model (voice `af_heart`) and writes
   `timing.json` (when each line starts) and `narration.wav`.
3. `lips.json` is the narration's loudness per video frame (24 fps); it drives the presenter's mouth.
4. `gen_video2.py` builds an HTML page where every animation is a CSS animation timed to `timing.json`.
   The presenter is an original character drawn in SVG. Maps use CalEnviroScreen 4.0 tracts, EPA PM10
   monitors, and Natural Earth highways, borders and the Salton Sea outline.
5. `capture.js` (Playwright) seeks every animation to each frame time and saves 1920×1080 frames;
   ffmpeg joins the frames and the narration into `media/lithium-explainer.mp4`.

The model files and generated frames are not stored here (they are large). Paths in the scripts point
to the author's working folder.
