"""Safe errors for mandatory Try-On analysis stages."""


class TryOnAnalysisBundleFailure(RuntimeError):
    """Safe fail-closed error returned when one required analysis fails."""

    def __init__(self, *, safe_code: str = "required_try_on_analysis_failed") -> None:
        super().__init__(safe_code)
        self.safe_code = safe_code


class GarmentIdentityAnalysisFailure(RuntimeError):
    """Safe Garment Identity analysis failure."""

    def __init__(self, *, safe_code: str) -> None:
        super().__init__(safe_code)
        self.safe_code = safe_code


class MaterialTextureAnalysisFailure(RuntimeError):
    """Safe Material / Texture analysis failure."""

    def __init__(self, *, safe_code: str) -> None:
        super().__init__(safe_code)
        self.safe_code = safe_code

