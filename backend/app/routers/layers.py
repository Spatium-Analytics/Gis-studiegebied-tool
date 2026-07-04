from fastapi import APIRouter

from app.layers_registry import LAYERS
from app.models import LayerManifestEntry

router = APIRouter()


@router.get("/layers", response_model=list[LayerManifestEntry])
def list_layers() -> list[LayerManifestEntry]:
    return [
        LayerManifestEntry(
            key=layer.key,
            label=layer.label,
            description=layer.description,
            output_kind=layer.output_kind,
            enabled=layer.enabled,
            notes=layer.notes,
            service_type=layer.service_type,
            base_url=layer.base_url,
            collection_or_coverage=layer.collection_or_coverage,
        )
        for layer in LAYERS
    ]
