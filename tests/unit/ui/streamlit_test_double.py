import sys
import types


class SessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class _ContextManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeStreamlit(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self._reset_state()

    def _reset_state(self):
        self.session_state = SessionState()
        self.markdowns = []
        self.infos = []
        self.warnings = []
        self.errors = []
        self.successes = []
        self.writes = []
        self.metrics = []
        self.json_payloads = []
        self.expanders = []
        self.tab_sets = []
        self.page_config = None
        self.rerun_called = False
        self.button_responses = {}
        self.text_area_responses = {}
        self.multiselect_responses = {}
        self.text_input_responses = {}
        self.slider_responses = {}
        self.number_input_responses = {}

    @staticmethod
    def cache_resource(func):
        return func

    def set_page_config(self, **kwargs):
        self.page_config = kwargs

    def markdown(self, text, unsafe_allow_html=False):
        self.markdowns.append(text)

    def info(self, text):
        self.infos.append(text)

    def warning(self, text):
        self.warnings.append(text)

    def error(self, text):
        self.errors.append(text)

    def success(self, text):
        self.successes.append(text)

    def write(self, text):
        self.writes.append(text)

    def subheader(self, text):
        self.writes.append(text)

    def metric(self, label, value, delta=None):
        self.metrics.append((label, value, delta))

    def json(self, payload):
        self.json_payloads.append(payload)

    def columns(self, spec):
        count = len(spec) if isinstance(spec, list) else int(spec)
        return [_ContextManager() for _ in range(count)]

    def tabs(self, labels):
        self.tab_sets.append(list(labels))
        return [_ContextManager() for _ in labels]

    def expander(self, label, expanded=False):
        self.expanders.append((label, expanded))
        return _ContextManager()

    def spinner(self, text):
        self.writes.append(text)
        return _ContextManager()

    def rerun(self):
        self.rerun_called = True

    def button(self, label, key=None, **kwargs):
        response_key = key or label
        return self.button_responses.get(response_key, False)

    def text_area(self, label, value="", key=None, **kwargs):
        response_key = key or label
        return self.text_area_responses.get(response_key, value)

    def multiselect(self, label, options, default=None, key=None, **kwargs):
        response_key = key or label
        return self.multiselect_responses.get(response_key, default or [])

    def text_input(self, label, value="", key=None, **kwargs):
        response_key = key or label
        return self.text_input_responses.get(response_key, value)

    def slider(self, label, value=0, key=None, **kwargs):
        response_key = key or label
        return self.slider_responses.get(response_key, value)

    def number_input(self, label, value=0, key=None, **kwargs):
        response_key = key or label
        return self.number_input_responses.get(response_key, value)


def install_streamlit_test_double():
    existing = sys.modules.get("streamlit")
    if isinstance(existing, FakeStreamlit):
        existing._reset_state()
        fake_streamlit = existing
    else:
        fake_streamlit = FakeStreamlit()
        sys.modules["streamlit"] = fake_streamlit

    streamlit_autorefresh = types.ModuleType("streamlit_autorefresh")
    streamlit_autorefresh.st_autorefresh = lambda *args, **kwargs: None
    sys.modules["streamlit_autorefresh"] = streamlit_autorefresh

    return fake_streamlit
