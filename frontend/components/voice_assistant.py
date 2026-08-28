"""Material Design 3 Voice Assistant Component for NCERT Tutor (Phases 2, 4, 5, 9, 10, 11, 14, 20).

Provides:
- Client-side Web Speech API Speech-to-Text (STT) recording component with state machine
- Student review card with edit & direct submission
- Browser Web Speech Synthesis Text-to-Speech (TTS) audio player with Math-to-Speech
- 100% Ephemeral audio processing with zero server storage and zero extra API keys
"""

import json
import logging

import streamlit.components.v1 as components

from backend.ai.speech_math import prepare_text_for_speech

logger = logging.getLogger(__name__)


def render_voice_recorder_component(
    component_key: str = "tutor_voice_recorder",
    class_level: int = 10,
    subject: str = "Science",
) -> None:
    """
    Directly injects an interactive Web Speech Recognition microphone button into Streamlit's bottom chat input textbar.

    Zero separate UI cards or bars. When clicked, transcribes speech live into the text bar,
    tags voice input, and automatically submits on completion.
    """
    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8" />
    <style>
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
    </style>
    </head>
    <body>
    <script>
    (function initChatInputMic() {{
        function attachMicToInput() {{
            try {{
                const rootWin = window.parent || window;
                const rootDoc = rootWin.document;
                const chatContainer = rootDoc.querySelector('[data-testid="stChatInput"]');
                if (!chatContainer) {{
                    setTimeout(attachMicToInput, 150);
                    return;
                }}

                const submitBtn = chatContainer.querySelector('button[data-testid="stChatInputSubmitButton"]');
                const textArea = chatContainer.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (!textArea) {{
                    setTimeout(attachMicToInput, 150);
                    return;
                }}

                // Remove previous zombie mic button if exists to guarantee live listener binding
                let existingMic = rootDoc.getElementById("stChatInputDirectMicBtn");
                if (existingMic) {{
                    existingMic.remove();
                }}

                const micBtn = rootDoc.createElement("button");
                micBtn.id = "stChatInputDirectMicBtn";
                micBtn.type = "button";
                micBtn.title = "Speak your doubt (Click to start/stop)";
                micBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" style="pointer-events: none; display: block;">
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                        <line x1="12" x2="12" y1="19" y2="22"/>
                    </svg>
                `;
                micBtn.setAttribute("style", `
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    background: transparent !important;
                    color: #fbbf24 !important;
                    border: none !important;
                    border-radius: 50% !important;
                    width: 34px !important;
                    height: 34px !important;
                    margin-right: 4px !important;
                    cursor: pointer !important;
                    pointer-events: auto !important;
                    transition: all 0.2s ease !important;
                    padding: 4px !important;
                    flex-shrink: 0 !important;
                    align-self: center !important;
                    z-index: 1000 !important;
                `);

                micBtn.onmouseenter = () => {{
                    if (!micBtn.classList.contains("recording")) {{
                        micBtn.style.background = "rgba(251, 191, 36, 0.16)";
                        micBtn.style.color = "#fef3c7";
                        micBtn.style.transform = "scale(1.08)";
                    }}
                }};
                micBtn.onmouseleave = () => {{
                    if (!micBtn.classList.contains("recording")) {{
                        micBtn.style.background = "transparent";
                        micBtn.style.color = "#fbbf24";
                        micBtn.style.transform = "scale(1.0)";
                    }}
                }};

                const SpeechRec = (rootWin.SpeechRecognition || rootWin.webkitSpeechRecognition || window.SpeechRecognition || window.webkitSpeechRecognition);

                if (!SpeechRec) {{
                    micBtn.title = "Speech recognition is not supported in this browser";
                    micBtn.style.opacity = "0.35";
                    micBtn.style.cursor = "not-allowed";
                }} else {{
                    let recognition = new SpeechRec();
                    recognition.continuous = false;
                    recognition.interimResults = true;
                    recognition.lang = "en-IN";
                    let isRecording = false;
                    let finalTranscript = "";

                    function resetMic() {{
                        isRecording = false;
                        micBtn.classList.remove("recording");
                        micBtn.style.background = "transparent";
                        micBtn.style.color = "#fbbf24";
                        micBtn.style.boxShadow = "none";
                        micBtn.style.transform = "scale(1.0)";
                        textArea.placeholder = "Ask any question from NCERT Class {class_level} {subject} or your notes...";
                    }}

                    recognition.onstart = () => {{
                        isRecording = true;
                        micBtn.classList.add("recording");
                        micBtn.style.background = "#ef4444";
                        micBtn.style.color = "#ffffff";
                        micBtn.style.boxShadow = "0 0 12px rgba(239, 68, 68, 0.9)";
                        micBtn.style.transform = "scale(1.12)";
                        textArea.placeholder = " Listening... Speak your doubt now (Click mic to stop)";
                    }};

                    recognition.onresult = (event) => {{
                        let interim = "";
                        for (let i = event.resultIndex; i < event.results.length; ++i) {{
                            if (event.results[i].isFinal) {{
                                finalTranscript += event.results[i][0].transcript;
                            }} else {{
                                interim += event.results[i][0].transcript;
                            }}
                        }}
                        const liveText = finalTranscript + (interim ? " " + interim : "");
                        if (liveText.trim()) {{
                            const nativeSetter = Object.getOwnPropertyDescriptor(rootWin.HTMLTextAreaElement.prototype, "value").set;
                            if (nativeSetter) nativeSetter.call(textArea, liveText);
                            else textArea.value = liveText;
                            textArea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                    }};

                    recognition.onerror = (e) => {{
                        console.error("Speech recognition error:", e);
                        resetMic();
                        if (e.error === "not-allowed") {{
                            alert("Microphone permission was denied. Please allow microphone access in your browser settings to speak.");
                        }}
                    }};

                    recognition.onend = () => {{
                        resetMic();
                        if (finalTranscript.trim()) {{
                            // Tag voice input with invisible marker \u200b[voice]
                            const voicePrompt = finalTranscript.trim() + "\u200b[voice]";
                            const nativeSetter = Object.getOwnPropertyDescriptor(rootWin.HTMLTextAreaElement.prototype, "value").set;
                            if (nativeSetter) nativeSetter.call(textArea, voicePrompt);
                            else textArea.value = voicePrompt;
                            textArea.dispatchEvent(new Event('input', {{ bubbles: true }}));

                            setTimeout(() => {{
                                const currentSubmitBtn = chatContainer.querySelector('button[data-testid="stChatInputSubmitButton"]');
                                if (currentSubmitBtn && !currentSubmitBtn.disabled) {{
                                    currentSubmitBtn.click();
                                }} else {{
                                    textArea.dispatchEvent(new KeyboardEvent('keydown', {{
                                        key: 'Enter',
                                        code: 'Enter',
                                        keyCode: 13,
                                        which: 13,
                                        bubbles: true
                                    }}));
                                }}
                            }}, 250);
                        }}
                    }};

                    function handleMicTrigger(e) {{
                        if (e) {{
                            e.preventDefault();
                            e.stopPropagation();
                        }}
                        if (isRecording) {{
                            recognition.stop();
                        }} else {{
                            finalTranscript = "";
                            try {{
                                recognition.start();
                            }} catch (err) {{
                                console.error("Start recording error:", err);
                            }}
                        }}
                    }}

                    micBtn.onclick = handleMicTrigger;
                    micBtn.onpointerdown = (e) => {{ e.stopPropagation(); }};
                    micBtn.onmousedown = (e) => {{ e.stopPropagation(); }};
                }}

                // Place mic button immediately before the submit button inside the textbar
                if (submitBtn && submitBtn.parentNode) {{
                    submitBtn.parentNode.insertBefore(micBtn, submitBtn);
                }} else {{
                    chatContainer.appendChild(micBtn);
                }}
            }} catch (err) {{
                console.error("Chat input mic error:", err);
            }}
        }}

        attachMicToInput();
        setInterval(attachMicToInput, 1200);
    }})();
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=0, scrolling=False)


render_bottom_voice_mic = render_voice_recorder_component


def render_tts_player_component(
    display_text: str,
    message_idx: int,
    button_label: str = "Listen to Answer",
    auto_play: bool = False,
) -> None:
    """
    Renders a client-side Web Speech Synthesis (TTS) audio player underneath a Tutor response.

    Converts mathematical expressions to speech phonetics, strips citations,
    and supports seamless rate changing from the current word position without restarting.
    """
    speech_text = prepare_text_for_speech(display_text)
    if not speech_text or len(speech_text.strip()) < 3:
        return

    # Escape speech text safely for JS string literal
    escaped_speech = json.dumps(speech_text)

    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}
        body {{
            background: transparent;
            color: #dac7b8;
            padding: 4px 0;
            user-select: none;
        }}
        .tts-row {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(35, 27, 22, 0.9);
            border: 1px solid #6b584c;
            border-radius: 8px;
            padding: 4px 10px;
        }}
        .btn-tts {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: transparent;
            color: #fbbf24;
            border: none;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 6px;
            transition: all 0.2s ease;
        }}
        .btn-tts:hover {{
            background: rgba(251, 191, 36, 0.15);
            color: #fef3c7;
        }}
        .btn-tts.active {{
            background: #fbbf24;
            color: #191310;
        }}
        .btn-ctrl {{
            display: inline-flex;
            align-items: center;
            background: transparent;
            color: #dac7b8;
            border: none;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            padding: 4px 6px;
            border-radius: 4px;
        }}
        .btn-ctrl:hover {{
            color: #faf0e6;
            background: rgba(250, 240, 230, 0.1);
        }}
        .rate-select {{
            background: #191310;
            color: #dac7b8;
            border: 1px solid #3f3129;
            border-radius: 4px;
            font-size: 0.75rem;
            padding: 2px 4px;
            cursor: pointer;
        }}
    </style>
    </head>
    <body>
    <div class="tts-row">
        <button id="playBtn_{message_idx}" class="btn-tts" onclick="togglePlay()">
            <span id="playIcon_{message_idx}"></span> <span id="playLabel_{message_idx}">{button_label}</span>
        </button>
        <button id="pauseBtn_{message_idx}" class="btn-ctrl" onclick="pauseAudio()" style="display: none;" title="Pause">
             Pause
        </button>
        <button id="stopBtn_{message_idx}" class="btn-ctrl" onclick="stopAudio()" style="display: none;" title="Stop">
             Stop
        </button>
        <select id="rateSelect_{message_idx}" class="rate-select" onchange="changeRate()" title="Speech Speed">
            <option value="0.9">0.9x</option>
            <option value="1.0" selected>1.0x</option>
            <option value="1.15">1.15x</option>
            <option value="1.3">1.3x</option>
        </select>
    </div>

    <script>
        const textToSpeak = {escaped_speech};
        const playBtn = document.getElementById("playBtn_{message_idx}");
        const playIcon = document.getElementById("playIcon_{message_idx}");
        const playLabel = document.getElementById("playLabel_{message_idx}");
        const pauseBtn = document.getElementById("pauseBtn_{message_idx}");
        const stopBtn = document.getElementById("stopBtn_{message_idx}");
        const rateSelect = document.getElementById("rateSelect_{message_idx}");

        let utterance = null;
        let isSpeaking = false;
        let isPaused = false;
        let currentCharOffset = 0;

        function startSpeakingFromOffset(offset) {{
            window.speechSynthesis.cancel();

            const textRemaining = textToSpeak.slice(offset) || textToSpeak;
            utterance = new SpeechSynthesisUtterance(textRemaining);
            utterance.rate = parseFloat(rateSelect.value) || 1.0;
            utterance.pitch = 1.0;
            utterance.lang = "en-IN";

            const baseOffset = offset;
            utterance.onboundary = (event) => {{
                if (typeof event.charIndex === "number") {{
                    currentCharOffset = baseOffset + event.charIndex;
                }}
            }};

            utterance.onstart = () => {{
                isSpeaking = true;
                isPaused = false;
                playBtn.className = "btn-tts active";
                playIcon.innerText = "";
                playLabel.innerText = "Playing...";
                pauseBtn.style.display = "inline-flex";
                stopBtn.style.display = "inline-flex";
            }};

            utterance.onend = () => {{
                currentCharOffset = 0;
                resetTTSUI();
            }};

            utterance.onerror = (e) => {{
                console.error("TTS Error:", e);
                currentCharOffset = 0;
                resetTTSUI();
            }};

            window.speechSynthesis.speak(utterance);
        }}

        function togglePlay() {{
            if (!("speechSynthesis" in window)) {{
                alert("Speech Synthesis is not supported in this browser.");
                return;
            }}

            if (isPaused) {{
                window.speechSynthesis.resume();
                isPaused = false;
                playIcon.innerText = "";
                playLabel.innerText = "Playing...";
                pauseBtn.innerText = " Pause";
                return;
            }}

            if (isSpeaking) {{
                stopAudio();
                return;
            }}

            currentCharOffset = 0;
            startSpeakingFromOffset(0);
        }}

        function pauseAudio() {{
            if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {{
                window.speechSynthesis.pause();
                isPaused = true;
                playIcon.innerText = "";
                playLabel.innerText = "Resume";
                pauseBtn.innerText = " Resume";
            }} else if (window.speechSynthesis.paused) {{
                window.speechSynthesis.resume();
                isPaused = false;
                playIcon.innerText = "";
                playLabel.innerText = "Playing...";
                pauseBtn.innerText = " Pause";
            }}
        }}

        function stopAudio() {{
            window.speechSynthesis.cancel();
            currentCharOffset = 0;
            resetTTSUI();
        }}

        function changeRate() {{
            if (isSpeaking && !isPaused) {{
                // Seamlessly continue speaking from current word/character offset at new rate
                startSpeakingFromOffset(currentCharOffset);
            }}
        }}

        function resetTTSUI() {{
            isSpeaking = false;
            isPaused = false;
            playBtn.className = "btn-tts";
            playIcon.innerText = "";
            playLabel.innerText = "{button_label}";
            pauseBtn.style.display = "none";
            stopBtn.style.display = "none";
        }}

        // Auto-play speech if requested
        window.addEventListener("DOMContentLoaded", () => {{
            const shouldAutoPlay = {json.dumps(auto_play)};
            if (shouldAutoPlay) {{
                setTimeout(() => {{
                    try {{
                        togglePlay();
                    }} catch (err) {{
                        console.log("Auto-TTS playback tolerance:", err);
                    }}
                }}, 350);
            }}
        }});
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=48, scrolling=False)
