from typing import TYPE_CHECKING, Union

from .llms import get_llm_object

if TYPE_CHECKING:
    from ..decorators.hook import SupportedHook
    from ..suit import Suit


class Kernel:
    def __init__(self, suit: "Suit"):
        # Load LLM & Embedder
        self.load_natural_language(suit)

    @property
    def supported_hook(self) -> "SupportedHook":
        from ..decorators import SupportedHook

        return SupportedHook

    def load_natural_language(self, suit: "Suit"):
        self.set_llm(self._load(self.supported_hook.SUIT_LLM, suit=suit, default="LLMChatOpenAI"))

    def _load(self, hook: "SupportedHook", *, suit: "Suit", default: str) -> Union[str, tuple[str, dict]]:
        return suit.execute_hook(hook, default=default)

    def set_llm(self, llm_cls_name: Union[str, tuple[str, dict]]) -> None:
        self.llm = get_llm_object(llm_cls_name)

    def find_llm(self, llm_cls_name: Union[str, tuple[str, dict]]) -> None:
        return get_llm_object(llm_cls_name)
