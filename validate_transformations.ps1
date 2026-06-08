$ErrorActionPreference = "Stop"

# Test ISO to MT transformation and validation
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  ISO 20022 to SWIFT MT103 VALIDATION" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$iso_xml = @'
<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>MSG20250120001</MsgId>
    </GrpHdr>
    <PmtInfo>
      <CdtTrfTxInf>
        <PmtId>
          <InstrId>INSTR123</InstrId>
        </PmtId>
        <Amt>
          <InstdAmt Ccy="USD">50000.00</InstdAmt>
        </Amt>
        <ChrgBr>SHAR</ChrgBr>
        <Dbtr>
          <Nm>JOHN DOE</Nm>
        </Dbtr>
        <Cdtr>
          <Nm>JANE SMITH</Nm>
        </Cdtr>
        <RmtInf>
          <Ustrd>Invoice 12345</Ustrd>
        </RmtInf>
      </CdtTrfTxInf>
    </PmtInfo>
  </CstmrCdtTrfInitn>
</Document>
'@

$body = @{
  message_id = "test-iso-001"
  mt_message = $iso_xml
} | ConvertTo-Json -Depth 10

try {
  Write-Host "`n[1] Transforming ISO to MT..." -ForegroundColor Yellow
  $transform_response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/reverse-transform" `
    -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
  $transform_result = $transform_response.Content | ConvertFrom-Json
  
  $mt103_output = $transform_result.mx_xml
  Write-Host "[OK] Transform successful" -ForegroundColor Green
  Write-Host "MT103 Output:`n$mt103_output`n" -ForegroundColor White

  Write-Host "[2] Validating MT103 output against SWIFT standards..." -ForegroundColor Yellow
  $validation_body = @{
    message_id = "test-iso-001-validation"
    mt_message = $mt103_output
  } | ConvertTo-Json -Depth 10

  $validation_response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/validate-transformation" `
    -Method POST -Body $validation_body -ContentType "application/json" -UseBasicParsing
  $validation_result = $validation_response.Content | ConvertFrom-Json

  Write-Host "`n[OK] Validation Results:" -ForegroundColor Green
  Write-Host "  Compliant: $($validation_result.is_compliant)" -ForegroundColor $(if($validation_result.is_compliant) { "Green" } else { "Red" })
  Write-Host "  Compliance Score: $($validation_result.compliance_score)%" -ForegroundColor Cyan
  Write-Host "  Direction: $($validation_result.direction)"
  
  if ($validation_result.correct_mappings.Count -gt 0) {
    Write-Host "`n[PASS] Correct Mappings:" -ForegroundColor Green
    $validation_result.correct_mappings | ForEach-Object { Write-Host "  - $_" }
  }
  
  if ($validation_result.missing_fields.Count -gt 0) {
    Write-Host "`n[FAIL] Missing Fields:" -ForegroundColor Red
    $validation_result.missing_fields | ForEach-Object { Write-Host "  - $_" }
  }
  
  if ($validation_result.validation_errors.Count -gt 0) {
    Write-Host "`n[ERROR] Validation Errors:" -ForegroundColor Red
    $validation_result.validation_errors | ForEach-Object { Write-Host "  - $_" }
  }
  
  if ($validation_result.suggested_fixes.Count -gt 0) {
    Write-Host "`n[FIX] Suggested Fixes:" -ForegroundColor Yellow
    $validation_result.suggested_fixes | ForEach-Object { Write-Host "  - $_" }
  }
}
catch {
  Write-Host "[ERROR] Exception: $_" -ForegroundColor Red
  if ($_.Exception.Response) {
    Write-Host $_.Exception.Response.Content -ForegroundColor DarkRed
  }
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "  VALIDATION TEST COMPLETE" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
