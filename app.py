import os
import hashlib
import streamlit as st
from game import State, INTRO, act, interpret
from llm import parse_action, narrate_v1_with_recovery, describe_v2, explain_error, list_models

def select_available_model():
    selected = st.session_state.get('available_model')
    if selected:
        st.session_state.model_id = selected

st.set_page_config(page_title='The Midnight Library', page_icon='🗝️', layout='centered')
if 'pending_model_id' in st.session_state:
    st.session_state.model_id = st.session_state.pop('pending_model_id')
with st.sidebar:
    st.title('🗝️ Game settings')
    version = st.selectbox('Version', ['Version 2 · Reliable', 'Version 1 · Interactive'])
    mode = st.radio('Game Master', ['Offline demo', 'Gemini API'])
    key = st.text_input('Gemini API key', type='password', value=os.getenv('GEMINI_API_KEY', '')).strip()
    st.session_state.setdefault('model_id', os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'))
    model = st.text_input('Gemini model', key='model_id').strip()
    st.caption('Use a Google AI Studio project with free-tier access. Model availability and quota depend on your account. Keys stay in this session and are not written to disk.')
    restart = st.button('Restart game', width='stretch', key='restart')
    fingerprint = hashlib.sha256(key.encode()).hexdigest()
    if st.session_state.get('model_key_fingerprint') != fingerprint:
        st.session_state.model_key_fingerprint = fingerprint
        st.session_state.model_names = []
        st.session_state.pop('available_model', None)
    if st.button('Load available models', disabled=not key or mode != 'Gemini API', key='load_models'):
        try:
            with st.spinner('Checking Gemini models…'):
                st.session_state.model_names = list_models(key)
            if not st.session_state.model_names:
                st.warning('No compatible generateContent models were found for this key. Antigravity agents use a different API. Check access to Gemini text models in Google AI Studio.')
        except Exception as error:
            st.session_state.model_names = []
            st.error(explain_error(error))
    if st.session_state.get('model_names'):
        st.selectbox('Available Gemini models', st.session_state.model_names, index=None,
                     placeholder='Select a model to use', key='available_model', on_change=select_available_model)
        st.caption('Selecting a model updates the Gemini model field above. Listing a model does not guarantee free quota or access to every feature.')
    st.caption('One action per message. Try “examine the bookshelf”, “take the key”, or “enter 123 on the drawer”.')

identity = (version, mode)
if restart or st.session_state.get('identity') != identity:
    st.session_state.identity = identity
    st.session_state.game = State()
    st.session_state.messages = [{'role': 'assistant', 'content': INTRO}]
    st.session_state.v1_escaped = False
    st.session_state.provider_notice = ''

st.caption('AN INTERACTIVE MYSTERY')
st.title('The Midnight Library')
st.write('Five objects. Three puzzles. One way out.')
reliable = version.startswith('Version 2')
online = mode == 'Gemini API'
if not online:
    st.info('Offline demo: a Python game engine responds to supported commands. Select Gemini API for the LLM experience. Both offline versions use the same validated engine; this mode does not demonstrate Version 1’s LLM weaknesses.')
if online and st.session_state.get('provider_notice'):
    st.warning(st.session_state.provider_notice)
if reliable:
    s = st.session_state.game
    st.progress(len(s.solved) / 3, text=f'{len(s.solved)} / 3 puzzles solved · {s.turns} actions')
    st.caption('Inventory: ' + (', '.join(s.inventory) or 'empty'))
done = st.session_state.game.escaped if reliable or not online else st.session_state.v1_escaped
for m in st.session_state.messages:
    with st.chat_message(m['role']): st.write(m['content'])
if done: st.success('You escaped! Restart to enter the library again.')
message = st.chat_input('What will you investigate?', disabled=done, max_chars=1500, key='action')
if message:
    if online and not key:
        st.warning('Enter a Gemini API key in settings, or choose Offline demo.')
    else:
        history = st.session_state.messages
        st.session_state.provider_notice = ''
        with st.spinner('The library listens…'):
            if online and not reliable:
                try:
                    reply, used_model = narrate_v1_with_recovery(key, model, history, message)
                    if used_model != model:
                        st.session_state.pending_model_id = used_model
                        st.session_state.provider_notice = f'The selected model was unavailable (404). Retried this turn successfully with {used_model}; the model setting has been updated.'
                    st.session_state.v1_escaped = '[ESCAPED]' in reply
                    reply = reply.replace('[ESCAPED]', '')
                except Exception as error:
                    st.error(explain_error(error) + ' Your turn was not submitted; your previous progress is preserved. Send your message again when ready.')
                    st.stop()
            else:
                try:
                    action = parse_action(key, model, message) if online else interpret(message)
                except Exception as error:
                    st.session_state.provider_notice = explain_error(error) + ' This turn used the offline command parser.'
                    action = interpret(message)
                reply = act(st.session_state.game, action)
                if online:
                    try: reply = describe_v2(key, model, reply)
                    except Exception as error:
                        if not st.session_state.provider_notice:
                            st.session_state.provider_notice = explain_error(error) + ' This turn used the canonical Python narration.'
        history.extend([{'role': 'user', 'content': message}, {'role': 'assistant', 'content': reply}])
        st.rerun()
