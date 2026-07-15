function doPost(e) {
  const spreadsheetId = 'YOUR_GOOGLE_SHEETS_ID';
  const sheetName = 'visit_history';
  const spreadsheet = SpreadsheetApp.openById(spreadsheetId);
  const sheet = spreadsheet.getSheetByName(sheetName) || spreadsheet.insertSheet(sheetName);

  const headers = [
    'date',
    'restaurant_id',
    'restaurant_name',
    'party_size',
    'decision',
    'base_address',
    'dong_name',
    'weather_summary',
    'selected_at',
    'place_url',
    'main_menu',
    'estimated_calories',
  ];

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  }

  try {
    const payload = JSON.parse(e.postData.contents || '{}');
    sheet.appendRow([
      payload.date || '',
      payload.restaurant_id || '',
      payload.restaurant_name || '',
      payload.party_size || '',
      payload.decision || '',
      payload.base_address || '',
      payload.dong_name || '',
      payload.weather_summary || '',
      payload.selected_at || '',
      payload.place_url || '',
      payload.main_menu || '',
      payload.estimated_calories || '',
    ]);

    return ContentService.createTextOutput(
      JSON.stringify({ ok: true, message: '저장 완료' }),
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({ ok: false, message: String(error) }),
    ).setMimeType(ContentService.MimeType.JSON);
  }
}
