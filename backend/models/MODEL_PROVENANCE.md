# Tassel Model Provenance

Verified on 25 July 2026.

| Item | Value |
|---|---|
| Original training filename | `best_pre_multicountry_20260725.pt` |
| Runtime filename | `best.pt` |
| Runtime path | `backend/models/best.pt` |
| Size | 20,405,573 bytes |
| SHA-256 | `37BCA6B8E817D911424DBD22F720F9CBE00248036E0FC6305EF853F8B38D9913` |

The original file and the runtime file were compared byte-for-byte through
their size and SHA-256 digest. They are the same model. The shorter runtime
name is intentional because `backend/inference.py` loads
`backend/models/best.pt`.

Acceptance inference on `ai/results/DJI_0243 (2)_annotated.jpg` produced 121
tassel boxes in fast CPU mode, confirming that the deployed artifact loads and
runs through the project inference path.
