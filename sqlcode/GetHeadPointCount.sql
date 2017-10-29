SELECT tar_token.ID, Documents.NAME, COUNT(pre_token.ID) as total_tokens, SUM(LENGTH(pre_token.surface)) as total_chars FROM
TOKENS as pre_token ,
TOKENS as tar_token , Documents
where pre_token.DOCUMENT_ID == tar_token.DOCUMENT_ID and pre_token.ID < tar_token.id and tar_token.DOCUMENT_ID == Documents.ID
and
tar_token.id IN (
	'297960',
	'631043',
	'585968',
	'729314'
)
GROUP BY tar_token.DOCUMENT_ID
;