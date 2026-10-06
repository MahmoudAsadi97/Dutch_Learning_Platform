"""Expected failures the client can act on.

Every domain raises a subclass of `DomainError`. The API turns it into one JSON body,
`{"detail": <sentence>, "code": <stable identifier>, "request_id": ...}` plus any `params`, through the
handler in `dlp.api.errors`. `code` is what the web app maps to copy in the learner's languages; `detail`
is the English sentence shown until then. `persist` marks a failure after which the work already done
(usage rows, a failed turn) must be committed rather than rolled back; the request layer honours it.
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    status_code: int = 400
    code: str = "domain_error"

    def __init__(self, detail: str, status_code: int | None = None, *, code: str | None = None,
                 params: dict[str, Any] | None = None, persist: bool = False) -> None:
        super().__init__(detail)
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.params = dict(params or {})
        self.persist = persist

    @property
    def reason(self) -> str:
        """Older call sites read `.reason`; it is the same sentence as `.detail`."""
        return self.detail

    def body(self, request_id: str = "") -> dict[str, Any]:
        return {"detail": self.detail, "code": self.code, "request_id": request_id, **self.params}
