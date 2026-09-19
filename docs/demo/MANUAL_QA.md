# SafetyLens Manual QA Checklist

Use this checklist for the demo-help route and the current Stage 3 video workflow. Record
only what was actually observed on the tested commit. A “not tested” result is valid and
preferable to inferring a pass.

## Test record

| Field | Value |
| --- | --- |
| Commit tested | `103df58` plus uncommitted Abhinav demo-support files |
| Tester | Abhinav |
| Environment | Local Windows development environment |
| Backend mode | Record live API, Offline Demo Mode, or unavailable API |
| Test video | Record filename, source permission, format, duration, and size |
| Date | 2026-09-19 |

## Results

| Area | Steps | Expected result | Actual result | Status |
| --- | --- | --- | --- | --- |
| App loads | Start the backend and frontend, then open `/demo-help`. | The guide renders with its four demo steps, route links, and rehearsal checklist. | Pass. The route rendered the expected steps and local checkbox behavior in a browser. One existing Base UI warning originates in the shared `TopNavigation` component. | Pass |
| Live Monitor upload | Open `/monitor`, select **Upload Demo Video**, and upload a permitted short MP4, MOV, or WebM clip. | The API accepts the upload and displays processing progress. Offline Demo Mode does not pretend an upload succeeded. | Not yet tested. | Not tested |
| Playback and frame timeline | After processing completes, open the uploaded recording and review playback, seeking, and the candidate-frame timeline. | Video playback and frame candidates are visible; candidates are not described as confirmed incident evidence. | Not yet tested. | Not tested |
| Backend disconnected state | Stop or make the backend unavailable, restart the frontend if needed, then visit `/demo-help` and `/monitor`. | The UI clearly displays its API/offline state. Upload remains unavailable rather than simulated as a success. | Pass. `/monitor` displayed **Offline Demo Mode**, an API-unavailable message, and an unavailable video library rather than a simulated upload success. | Pass |
| Narrow layout | At approximately 390 px wide, review `/demo-help` with keyboard-only navigation. | Cards remain readable, links and checkboxes can receive focus, and no horizontal scrolling is introduced. | Layout pass. At a 390 px viewport, document width was 375 px with no horizontal overflow. Keyboard-only traversal was not separately tested. | Not tested |

## Test notes

- The rehearsal checkboxes are local UI state only. They do not process an incident, approve
  an action, or persist a safety decision.
- The current Stage 3 workflow prepares video and evidence-candidate frames. Multimodal AI
  verification, video-driven procedure retrieval, notifications, and report generation remain
  later stages unless an integrated release demonstrates otherwise.
- Record any issue with a reproducible path, browser/device, API mode, and the exact tested
  commit before handing it to the owning teammate.
