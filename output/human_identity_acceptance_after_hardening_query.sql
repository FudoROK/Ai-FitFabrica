
WITH input(job_id, file_name) AS (VALUES
('try_on_21779db9d9b541d7a983dde6355ff728', 'blurry_dark.jpg'),
('try_on_b67af7d176b64d62b0e9992b938bd701', 'cropped_face_only.jpg'),
('try_on_c58f1d8b513e4e1e831df63d475922db', 'face_hidden.jpg'),
('try_on_c8b1d1401aab4ee29bd97945305a582b', 'good_front.jpg'),
('try_on_b7b55791c96240329f9021e065c590c4', 'multiple_people.jpg'),
('try_on_e76bff9a50c542fd98ec64ec5e71a1a9', 'multiple_people_masks.jpg'),
('try_on_f54ab6cb560f476f9292716d19765359', 'not_human.jpg'),
('try_on_c79d620628e04bd08752cd5ee107b1d3', 'side_pose.jpg')
)
SELECT
  input.file_name,
  input.job_id,
  jobs.status AS job_status,
  errors.code AS job_error_code,
  errors.message AS job_error_message,
  errors.details AS job_error_details,
  human.verdict,
  human.confidence,
  human.uncertainty_level,
  human.analysis->>'contract_version' AS human_contract,
  human.analysis->>'face_visibility' AS face_visibility,
  human.analysis->>'subject_count' AS subject_count,
  human.analysis->>'crop_quality' AS crop_quality,
  human.analysis->>'try_on_body_coverage' AS body_coverage,
  human.analysis->>'occlusion_risk' AS occlusion_risk,
  human.analysis->'required_regions_missing' AS required_regions_missing,
  human.analysis->'rejection_reasons' AS rejection_reasons
FROM input
LEFT JOIN try_on_jobs jobs ON jobs.job_id = input.job_id
LEFT JOIN try_on_errors errors ON errors.job_id = input.job_id
LEFT JOIN try_on_human_identity_analyses human ON human.job_id = input.job_id
ORDER BY input.file_name;
