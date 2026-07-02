
WITH input(job_id, file_name) AS (VALUES
('try_on_1d336683c6f8403cbde81407f21b4166', 'blurry_dark.jpg'),
('try_on_834eb7a86b464534baa3d0f93818327f', 'cropped_face_only.jpg'),
('try_on_5aad047f445e43c49dcdd6bf837f8fb1', 'face_hidden.jpg'),
('try_on_c6064bc811914763ab0665bd7c120cb3', 'good_front.jpg'),
('try_on_939c024d793f4af3ae2bb0e84720fba8', 'multiple_people.jpg'),
('try_on_f4d27a9bb6f44f4080d3a51ed50b578b', 'multiple_people_masks.jpg'),
('try_on_947d0f391d164dc29056ae746bf6291d', 'not_human.jpg'),
('try_on_ecdbec2f8e9a457bb32b9f74a760975b', 'side_pose.jpg')
)
SELECT
  input.file_name,
  input.job_id,
  jobs.status AS job_status,
  human.verdict,
  human.confidence,
  human.uncertainty_level,
  human.analysis->>'face_visibility' AS face_visibility,
  human.analysis->>'pose_summary' AS pose_summary,
  human.analysis->'rejection_reasons' AS rejection_reasons,
  human.analysis->'limitations' AS limitations,
  human.analysis->'unknowns' AS unknowns
FROM input
LEFT JOIN try_on_jobs jobs ON jobs.job_id = input.job_id
LEFT JOIN try_on_human_identity_analyses human ON human.job_id = input.job_id
ORDER BY input.file_name;
