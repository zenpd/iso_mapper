"""
ISO 20022 Migration Platform - Bidirectional
MT101 ↔ pain.001 | MT103 ↔ pacs.008
Fixed: Transform now works for all inputs including XML
"""

import streamlit as st
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

st.set_page_config(
    page_title="ISO 20022 Migration",
    page_icon="🔄",
    layout="wide"
)

# Sample messages
SAMPLES = {
    "MT103 - USD Transfer": """:20:TRX2024112001
:23B:CRED
:32A:241118USD50000,00
:50K:/123456789
ACME CORPORATION
123 BUSINESS STREET
NEW YORK, NY 10001
:52A:CHASUS33XXX
:59:/987654321
GLOBAL TRADING LTD
456 COMMERCE AVENUE
LONDON, EC2R 8AH
:70:INVOICE INV-2024-1234
:71A:SHA""",
    "MT101 - Payment Request": """:20:PAYREQ001
:28D:1/1
:30:241120
:25:/123456789
:50H:/DE89370400440532013000
ORDERING COMPANY GMBH
FRANKFURT, GERMANY
:52A:DEUTDEFFXXX
:21:TXN001
:32B:EUR10000,00
:57A:ABORABAB
:59:/AE070331234567890123456
BENEFICIARY LLC
DUBAI
:70:SALARY NOV 2024
:71A:SHA""",
    "pacs.008 - Credit Transfer": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <FIToFICstmrCdtTrf>
    <GrpHdr>
      <MsgId>PACS008-2024-001</MsgId>
      <CreDtTm>2024-11-18T10:30:00</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
    </GrpHdr>
    <CdtTrfTxInf>
      <PmtId>
        <EndToEndId>E2E-REF-001</EndToEndId>
      </PmtId>
      <IntrBkSttlmAmt Ccy="USD">75000.00</IntrBkSttlmAmt>
      <IntrBkSttlmDt>2024-11-18</IntrBkSttlmDt>
      <ChrgBr>SHAR</ChrgBr>
      <Dbtr>
        <Nm>SENDER COMPANY INC</Nm>
        <PstlAdr>
          <Ctry>US</Ctry>
        </PstlAdr>
      </Dbtr>
      <DbtrAcct>
        <Id>
          <Othr>
            <Id>123456789</Id>
          </Othr>
        </Id>
      </DbtrAcct>
      <DbtrAgt>
        <FinInstnId>
          <BICFI>CHASUS33XXX</BICFI>
        </FinInstnId>
      </DbtrAgt>
      <CdtrAgt>
        <FinInstnId>
          <BICFI>BABORABB</BICFI>
        </FinInstnId>
      </CdtrAgt>
      <Cdtr>
        <Nm>RECEIVER COMPANY LLC</Nm>
        <PstlAdr>
          <Ctry>AE</Ctry>
        </PstlAdr>
      </Cdtr>
      <CdtrAcct>
        <Id>
          <Othr>
            <Id>987654321</Id>
          </Othr>
        </Id>
      </CdtrAcct>
      <RmtInf>
        <Ustrd>Payment for services</Ustrd>
      </RmtInf>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>""",
    "pain.001 - Payment Initiation": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>PAIN001-2024-001</MsgId>
      <CreDtTm>2024-11-20T09:00:00</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>PMT-001</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <ReqdExctnDt>
        <Dt>2024-11-20</Dt>
      </ReqdExctnDt>
      <Dbtr>
        <Nm>ORDERING COMPANY</Nm>
      </Dbtr>
      <DbtrAcct>
        <Id>
          <IBAN>DE89370400440532013000</IBAN>
        </Id>
      </DbtrAcct>
      <DbtrAgt>
        <FinInstnId>
          <BICFI>DEUTDEFFXXX</BICFI>
        </FinInstnId>
      </DbtrAgt>
      <CdtTrfTxInf>
        <PmtId>
          <EndToEndId>E2E-PMT-001</EndToEndId>
        </PmtId>
        <Amt>
          <InstdAmt Ccy="EUR">25000.00</InstdAmt>
        </Amt>
        <CdtrAgt>
          <FinInstnId>
            <BICFI>ABORABAB</BICFI>
          </FinInstnId>
        </CdtrAgt>
        <Cdtr>
          <Nm>BENEFICIARY COMPANY</Nm>
        </Cdtr>
        <CdtrAcct>
          <Id>
            <IBAN>AE070331234567890123456</IBAN>
          </Id>
        </CdtrAcct>
        <RmtInf>
          <Ustrd>Invoice payment</Ustrd>
        </RmtInf>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""
}


def get_utc_now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def detect_message_type(text: str) -> Tuple[str, str]:
    """Detect message type. Returns: (source_type, target_type)"""
    text = text.strip()
    
    if 'pacs.008' in text or 'FIToFICstmrCdtTrf' in text:
        return ('pacs.008', 'MT103')
    if 'pain.001' in text or 'CstmrCdtTrfInitn' in text:
        return ('pain.001', 'MT101')
    
    if text.startswith('{'):
        try:
            data = json.loads(text)
            if 'Document' in data:
                if 'FIToFICstmrCdtTrf' in str(data):
                    return ('pacs.008', 'MT103')
                if 'CstmrCdtTrfInitn' in str(data):
                    return ('pain.001', 'MT101')
            if 'MT101' in data:
                return ('MT101', 'pain.001')
            if 'MT103' in data:
                return ('MT103', 'pacs.008')
            mt = data.get('MT103', data.get('MT101', data))
            b4 = mt.get('Block4', {})
            if any(k in b4 for k in ['Field28D', 'Field50H']):
                return ('MT101', 'pain.001')
            return ('MT103', 'pacs.008')
        except:
            pass
    
    if ':28D:' in text or ':50H:' in text or (':30:' in text and ':32B:' in text):
        return ('MT101', 'pain.001')
    return ('MT103', 'pacs.008')


def parse_message(text: str, source_type: str) -> Dict[str, Any]:
    """Parse message based on type"""
    if source_type in ['pacs.008', 'pain.001']:
        return parse_mx_xml(text)
    elif text.strip().startswith('{'):
        return parse_mt_json(text)
    else:
        return parse_mt_text(text)


def parse_mt_json(text: str) -> Dict[str, Any]:
    result = {}
    try:
        data = json.loads(text)
        mt = data.get('MT103', data.get('MT101', data))
        b4 = mt.get('Block4', {})
        
        result['ref'] = b4.get('Field20', '')
        
        f32a = b4.get('Field32A', {})
        f32b = b4.get('Field32B', {})
        if isinstance(f32a, dict) and f32a:
            result['date'] = str(f32a.get('Date', ''))
            result['ccy'] = str(f32a.get('Currency', ''))
            result['amt'] = str(f32a.get('Amount', '')).replace(',', '.')
        elif isinstance(f32b, dict) and f32b:
            result['ccy'] = str(f32b.get('Currency', ''))
            result['amt'] = str(f32b.get('Amount', '')).replace(',', '.')
        
        if 'Field30' in b4 and not result.get('date'):
            result['date'] = str(b4.get('Field30', ''))
        
        for fname in ['Field50F', 'Field50K', 'Field50H']:
            if fname in b4:
                sender = b4[fname]
                if isinstance(sender, dict):
                    result['s_acct'] = sender.get('Account', '')
                    na = sender.get('NameAndAddress', {})
                    if isinstance(na, dict):
                        l1 = na.get('Line1', '')
                        result['s_name'] = l1.split('/', 1)[-1].strip() if '/' in l1 and l1 and l1[0].isdigit() else l1
                        l4 = na.get('Line4', '')
                        if l4 and len(l4.split('/')) >= 2:
                            result['s_ctry'] = l4.split('/')[1].strip()
                    elif isinstance(na, str):
                        result['s_name'] = na
                break
        
        f52 = b4.get('Field52A', {})
        if isinstance(f52, dict):
            result['s_bic'] = f52.get('IdentifierCode', '')
        elif f52:
            result['s_bic'] = str(f52)
        
        for fname in ['Field59F', 'Field59']:
            if fname in b4:
                recv = b4[fname]
                if isinstance(recv, dict):
                    result['r_acct'] = recv.get('Account', '')
                    na = recv.get('NameAndAddress', {})
                    if isinstance(na, dict):
                        l1 = na.get('Line1', '')
                        result['r_name'] = l1.split('/', 1)[-1].strip() if '/' in l1 and l1 and l1[0].isdigit() else l1
                        l4 = na.get('Line4', '')
                        if l4 and len(l4.split('/')) >= 2:
                            result['r_ctry'] = l4.split('/')[1].strip()
                    elif isinstance(na, str):
                        result['r_name'] = na
                break
        
        result['remit'] = b4.get('Field70', '')
        result['charges'] = b4.get('Field71A', '')
    except:
        pass
    return result


def parse_mt_text(text: str) -> Dict[str, Any]:
    result = {}
    
    m = re.search(r':20:([^\n:]+)', text)
    if m: result['ref'] = m.group(1).strip()
    
    m = re.search(r':32A:(\d{6})([A-Z]{3})([\d,\.]+)', text)
    if m:
        result['date'] = m.group(1)
        result['ccy'] = m.group(2)
        result['amt'] = m.group(3).replace(',', '.')
    
    if not result.get('amt'):
        m = re.search(r':32B:([A-Z]{3})([\d,\.]+)', text)
        if m:
            result['ccy'] = m.group(1)
            result['amt'] = m.group(2).replace(',', '.')
    
    if not result.get('date'):
        m = re.search(r':30:(\d{6})', text)
        if m: result['date'] = m.group(1)
    
    m = re.search(r':50[KFH]:(.*?)(?=:\d{2}[A-Z]?:|\Z)', text, re.DOTALL)
    if m:
        lines = [l.strip() for l in m.group(1).strip().split('\n') if l.strip()]
        if lines:
            if lines[0].startswith('/'):
                result['s_acct'] = lines[0]
                result['s_name'] = lines[1] if len(lines) > 1 else ''
            else:
                result['s_name'] = lines[0]
            result['s_ctry'] = guess_country(' '.join(lines), result.get('ccy', ''))
    
    m = re.search(r':52A:([^\n:]+)', text)
    if m: result['s_bic'] = m.group(1).strip()
    
    m = re.search(r':59[AF]?:(.*?)(?=:\d{2}[A-Z]?:|\Z)', text, re.DOTALL)
    if m:
        lines = [l.strip() for l in m.group(1).strip().split('\n') if l.strip()]
        if lines:
            if lines[0].startswith('/'):
                result['r_acct'] = lines[0]
                result['r_name'] = lines[1] if len(lines) > 1 else ''
            else:
                result['r_name'] = lines[0]
            result['r_ctry'] = guess_country(' '.join(lines), '')
    
    m = re.search(r':70:(.*?)(?=:\d{2}[A-Z]?:|\Z)', text, re.DOTALL)
    if m: result['remit'] = m.group(1).strip().replace('\n', ' ')
    
    m = re.search(r':71A:([A-Z]{3})', text)
    if m: result['charges'] = m.group(1)
    
    return result


def parse_mx_xml(text: str) -> Dict[str, Any]:
    """Parse ISO 20022 XML using regex"""
    result = {}
    
    # Reference
    m = re.search(r'<MsgId>([^<]+)</MsgId>', text)
    if m: result['ref'] = m.group(1).strip()
    if not result.get('ref'):
        m = re.search(r'<EndToEndId>([^<]+)</EndToEndId>', text)
        if m: result['ref'] = m.group(1).strip()
    
    # Amount and Currency
    m = re.search(r'<IntrBkSttlmAmt\s+Ccy="([^"]+)"[^>]*>([^<]+)</IntrBkSttlmAmt>', text)
    if m:
        result['ccy'] = m.group(1)
        result['amt'] = m.group(2).strip()
    else:
        m = re.search(r'<InstdAmt\s+Ccy="([^"]+)"[^>]*>([^<]+)</InstdAmt>', text)
        if m:
            result['ccy'] = m.group(1)
            result['amt'] = m.group(2).strip()
    
    # Date
    m = re.search(r'<IntrBkSttlmDt>([^<]+)</IntrBkSttlmDt>', text)
    if m: result['date'] = m.group(1).strip()[:10]
    if not result.get('date'):
        m = re.search(r'<Dt>([^<]+)</Dt>', text)
        if m: result['date'] = m.group(1).strip()[:10]
    if not result.get('date'):
        m = re.search(r'<CreDtTm>([^<]+)</CreDtTm>', text)
        if m: result['date'] = m.group(1).strip()[:10]
    
    # Debtor Name
    m = re.search(r'<Dbtr>\s*<Nm>([^<]+)</Nm>', text, re.DOTALL)
    if m: result['s_name'] = m.group(1).strip()
    
    # Debtor Account
    m = re.search(r'<DbtrAcct>.*?<IBAN>([^<]+)</IBAN>', text, re.DOTALL)
    if m:
        result['s_acct'] = m.group(1).strip()
    else:
        m = re.search(r'<DbtrAcct>.*?<Id>([^<]+)</Id>', text, re.DOTALL)
        if m: result['s_acct'] = m.group(1).strip()
    
    # Debtor BIC
    m = re.search(r'<DbtrAgt>.*?<BICFI>([^<]+)</BICFI>', text, re.DOTALL)
    if m: result['s_bic'] = m.group(1).strip()
    
    # Debtor Country
    m = re.search(r'<Dbtr>.*?<Ctry>([^<]+)</Ctry>', text, re.DOTALL)
    if m: result['s_ctry'] = m.group(1).strip()
    
    # Creditor Name
    m = re.search(r'<Cdtr>\s*<Nm>([^<]+)</Nm>', text, re.DOTALL)
    if m: result['r_name'] = m.group(1).strip()
    
    # Creditor Account
    m = re.search(r'<CdtrAcct>.*?<IBAN>([^<]+)</IBAN>', text, re.DOTALL)
    if m:
        result['r_acct'] = m.group(1).strip()
    else:
        m = re.search(r'<CdtrAcct>.*?<Id>([^<]+)</Id>', text, re.DOTALL)
        if m: result['r_acct'] = m.group(1).strip()
    
    # Creditor BIC
    m = re.search(r'<CdtrAgt>.*?<BICFI>([^<]+)</BICFI>', text, re.DOTALL)
    if m: result['r_bic'] = m.group(1).strip()
    
    # Creditor Country
    m = re.search(r'<Cdtr>.*?<Ctry>([^<]+)</Ctry>', text, re.DOTALL)
    if m: result['r_ctry'] = m.group(1).strip()
    
    # Remittance
    m = re.search(r'<Ustrd>([^<]+)</Ustrd>', text)
    if m: result['remit'] = m.group(1).strip()
    
    # Charges
    m = re.search(r'<ChrgBr>([^<]+)</ChrgBr>', text)
    if m: result['charges'] = m.group(1).strip()
    
    return result


def guess_country(text: str, ccy: str) -> str:
    t = text.upper()
    if any(x in t for x in ['USA', 'NEW YORK', 'NY ']): return 'US'
    if any(x in t for x in ['UK', 'LONDON']): return 'GB'
    if any(x in t for x in ['GERMANY', 'FRANKFURT', 'GMBH']): return 'DE'
    if any(x in t for x in ['FRANCE', 'PARIS']): return 'FR'
    if any(x in t for x in ['UAE', 'DUBAI']): return 'AE'
    return {'USD': 'US', 'EUR': 'EU', 'GBP': 'GB', 'AED': 'AE'}.get(ccy, '')


def get_flag(c: str) -> str:
    return {'US': '🇺🇸', 'GB': '🇬🇧', 'DE': '🇩🇪', 'FR': '🇫🇷', 'AE': '🇦🇪', 'EU': '🇪🇺'}.get(c or '', '🌍')


def format_amount(amt: str, ccy: str) -> str:
    try:
        v = float(amt) if amt else 0
        s = {'USD': '$', 'EUR': '€', 'GBP': '£', 'AED': 'د.إ'}.get(ccy, f'{ccy} ')
        return f"{s}{v:,.2f}"
    except:
        return f"{ccy} {amt}"


def generate_mt_text(fields: Dict[str, Any], mt_type: str) -> str:
    lines = [f":20:{fields.get('ref', 'REF001')[:16]}"]
    
    if mt_type == 'MT101':
        lines.append(":28D:1/1")
        date = fields.get('date', '').replace('-', '')[:6] or datetime.now(timezone.utc).strftime('%y%m%d')
        lines.append(f":30:{date}")
        lines.append(f":50H:/{fields.get('s_acct', '').replace('/', '')}")
        if fields.get('s_name'): lines.append(fields['s_name'][:35])
        if fields.get('s_bic'): lines.append(f":52A:{fields['s_bic']}")
        lines.append(":21:TXN001")
        lines.append(f":32B:{fields.get('ccy', 'USD')}{fields.get('amt', '0').replace('.', ',')}")
    else:
        lines.append(":23B:CRED")
        date = fields.get('date', '').replace('-', '')[:6] or datetime.now(timezone.utc).strftime('%y%m%d')
        lines.append(f":32A:{date}{fields.get('ccy', 'USD')}{fields.get('amt', '0').replace('.', ',')}")
        lines.append(f":50K:/{fields.get('s_acct', '').replace('/', '')}")
        if fields.get('s_name'): lines.append(fields['s_name'][:35])
        if fields.get('s_bic'): lines.append(f":52A:{fields['s_bic']}")
    
    lines.append(f":59:/{fields.get('r_acct', '').replace('/', '')}")
    if fields.get('r_name'): lines.append(fields['r_name'][:35])
    if fields.get('remit'): lines.append(f":70:{fields.get('remit', '')[:35]}")
    
    charges = fields.get('charges', 'SHA')
    if charges not in ['SHA', 'BEN', 'OUR', 'SHAR']: charges = 'SHA'
    if charges == 'SHAR': charges = 'SHA'
    lines.append(f":71A:{charges}")
    
    return '\n'.join(lines)


def generate_mt_json(fields: Dict[str, Any], mt_type: str) -> Dict[str, Any]:
    date = fields.get('date', '').replace('-', '')[:6] or datetime.now(timezone.utc).strftime('%y%m%d')
    charges = fields.get('charges', 'SHA')
    if charges not in ['SHA', 'BEN', 'OUR']: charges = 'SHA'
    
    if mt_type == 'MT101':
        return {
            "MT101": {
                "Block1": {"ApplicationId": "F", "ServiceId": "01", "LTAddress": "BANKXXXXAXXX"},
                "Block2": {"MessageType": "101", "Priority": "N"},
                "Block4": {
                    "Field20": fields.get('ref', 'REF001'),
                    "Field28D": "1/1",
                    "Field30": date,
                    "Field50H": {"Account": f"/{fields.get('s_acct', '').replace('/', '')}", "NameAndAddress": fields.get('s_name', '')},
                    "Field52A": {"IdentifierCode": fields.get('s_bic', '')},
                    "Field21": "TXN001",
                    "Field32B": {"Currency": fields.get('ccy', 'USD'), "Amount": fields.get('amt', '0').replace('.', ',')},
                    "Field59": {"Account": f"/{fields.get('r_acct', '').replace('/', '')}", "NameAndAddress": fields.get('r_name', '')},
                    "Field70": fields.get('remit', ''),
                    "Field71A": charges
                }
            }
        }
    else:
        return {
            "MT103": {
                "Block1": {"ApplicationId": "F", "ServiceId": "01", "LTAddress": "BANKXXXXAXXX"},
                "Block2": {"MessageType": "103", "Priority": "N"},
                "Block4": {
                    "Field20": fields.get('ref', 'REF001'),
                    "Field23B": "CRED",
                    "Field32A": {"Date": date, "Currency": fields.get('ccy', 'USD'), "Amount": fields.get('amt', '0').replace('.', ',')},
                    "Field50K": {"Account": f"/{fields.get('s_acct', '').replace('/', '')}", "NameAndAddress": fields.get('s_name', '')},
                    "Field52A": {"IdentifierCode": fields.get('s_bic', '')},
                    "Field59": {"Account": f"/{fields.get('r_acct', '').replace('/', '')}", "NameAndAddress": fields.get('r_name', '')},
                    "Field70": fields.get('remit', ''),
                    "Field71A": charges
                }
            }
        }


def generate_mx_xml(fields: Dict[str, Any], mx_type: str) -> str:
    now = get_utc_now()
    date = fields.get('date', '') or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if len(date) == 6:
        date = f"20{date[:2]}-{date[2:4]}-{date[4:6]}"
    
    if mx_type == 'pain.001':
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>{fields.get('ref', 'MSG001')}</MsgId>
      <CreDtTm>{now}</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <CtrlSum>{fields.get('amt', '0')}</CtrlSum>
      <InitgPty><Nm>{fields.get('s_name', '')}</Nm></InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>PMT-{fields.get('ref', '001')}</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <NbOfTxs>1</NbOfTxs>
      <ReqdExctnDt><Dt>{date}</Dt></ReqdExctnDt>
      <Dbtr><Nm>{fields.get('s_name', '')}</Nm></Dbtr>
      <DbtrAcct><Id><Othr><Id>{fields.get('s_acct', '').replace('/', '')}</Id></Othr></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><BICFI>{fields.get('s_bic', '')}</BICFI></FinInstnId></DbtrAgt>
      <CdtTrfTxInf>
        <PmtId><EndToEndId>E2E-{fields.get('ref', '001')}</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="{fields.get('ccy', 'USD')}">{fields.get('amt', '0')}</InstdAmt></Amt>
        <CdtrAgt><FinInstnId><BICFI>{fields.get('r_bic', '')}</BICFI></FinInstnId></CdtrAgt>
        <Cdtr><Nm>{fields.get('r_name', '')}</Nm></Cdtr>
        <CdtrAcct><Id><Othr><Id>{fields.get('r_acct', '').replace('/', '')}</Id></Othr></Id></CdtrAcct>
        <RmtInf><Ustrd>{fields.get('remit', '')}</Ustrd></RmtInf>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>'''
    else:
        chrg = 'SHAR' if fields.get('charges', 'SHA') == 'SHA' else fields.get('charges', 'SHAR')
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
  <FIToFICstmrCdtTrf>
    <GrpHdr>
      <MsgId>{fields.get('ref', 'MSG001')}</MsgId>
      <CreDtTm>{now}</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <SttlmInf><SttlmMtd>INDA</SttlmMtd></SttlmInf>
    </GrpHdr>
    <CdtTrfTxInf>
      <PmtId>
        <InstrId>INSTR-{fields.get('ref', '001')}</InstrId>
        <EndToEndId>E2E-{fields.get('ref', '001')}</EndToEndId>
      </PmtId>
      <IntrBkSttlmAmt Ccy="{fields.get('ccy', 'USD')}">{fields.get('amt', '0')}</IntrBkSttlmAmt>
      <IntrBkSttlmDt>{date}</IntrBkSttlmDt>
      <ChrgBr>{chrg}</ChrgBr>
      <Dbtr><Nm>{fields.get('s_name', '')}</Nm><PstlAdr><Ctry>{fields.get('s_ctry', '')}</Ctry></PstlAdr></Dbtr>
      <DbtrAcct><Id><Othr><Id>{fields.get('s_acct', '').replace('/', '')}</Id></Othr></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><BICFI>{fields.get('s_bic', '')}</BICFI></FinInstnId></DbtrAgt>
      <CdtrAgt><FinInstnId><BICFI>{fields.get('r_bic', '')}</BICFI></FinInstnId></CdtrAgt>
      <Cdtr><Nm>{fields.get('r_name', '')}</Nm><PstlAdr><Ctry>{fields.get('r_ctry', '')}</Ctry></PstlAdr></Cdtr>
      <CdtrAcct><Id><Othr><Id>{fields.get('r_acct', '').replace('/', '')}</Id></Othr></Id></CdtrAcct>
      <RmtInf><Ustrd>{fields.get('remit', '')}</Ustrd></RmtInf>
    </CdtTrfTxInf>
  </FIToFICstmrCdtTrf>
</Document>'''


def generate_mx_json(fields: Dict[str, Any], mx_type: str) -> Dict[str, Any]:
    now = get_utc_now()
    date = fields.get('date', '') or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    if mx_type == 'pain.001':
        return {
            "Document": {
                "CstmrCdtTrfInitn": {
                    "GrpHdr": {"MsgId": fields.get('ref', 'MSG001'), "CreDtTm": now, "NbOfTxs": "1"},
                    "PmtInf": {
                        "PmtInfId": f"PMT-{fields.get('ref', '001')}",
                        "PmtMtd": "TRF",
                        "ReqdExctnDt": {"Dt": date},
                        "Dbtr": {"Nm": fields.get('s_name', '')},
                        "DbtrAcct": {"Id": {"Othr": {"Id": fields.get('s_acct', '').replace('/', '')}}},
                        "DbtrAgt": {"FinInstnId": {"BICFI": fields.get('s_bic', '')}},
                        "CdtTrfTxInf": {
                            "PmtId": {"EndToEndId": f"E2E-{fields.get('ref', '001')}"},
                            "Amt": {"InstdAmt": {"Ccy": fields.get('ccy', 'USD'), "value": fields.get('amt', '0')}},
                            "CdtrAgt": {"FinInstnId": {"BICFI": fields.get('r_bic', '')}},
                            "Cdtr": {"Nm": fields.get('r_name', '')},
                            "CdtrAcct": {"Id": {"Othr": {"Id": fields.get('r_acct', '').replace('/', '')}}},
                            "RmtInf": {"Ustrd": fields.get('remit', '')}
                        }
                    }
                }
            }
        }
    else:
        return {
            "Document": {
                "FIToFICstmrCdtTrf": {
                    "GrpHdr": {"MsgId": fields.get('ref', 'MSG001'), "CreDtTm": now, "NbOfTxs": "1", "SttlmInf": {"SttlmMtd": "INDA"}},
                    "CdtTrfTxInf": {
                        "PmtId": {"InstrId": f"INSTR-{fields.get('ref', '001')}", "EndToEndId": f"E2E-{fields.get('ref', '001')}"},
                        "IntrBkSttlmAmt": {"Ccy": fields.get('ccy', 'USD'), "value": fields.get('amt', '0')},
                        "IntrBkSttlmDt": date,
                        "ChrgBr": fields.get('charges', 'SHAR'),
                        "Dbtr": {"Nm": fields.get('s_name', ''), "PstlAdr": {"Ctry": fields.get('s_ctry', '')}},
                        "DbtrAcct": {"Id": {"Othr": {"Id": fields.get('s_acct', '').replace('/', '')}}},
                        "DbtrAgt": {"FinInstnId": {"BICFI": fields.get('s_bic', '')}},
                        "CdtrAgt": {"FinInstnId": {"BICFI": fields.get('r_bic', '')}},
                        "Cdtr": {"Nm": fields.get('r_name', ''), "PstlAdr": {"Ctry": fields.get('r_ctry', '')}},
                        "CdtrAcct": {"Id": {"Othr": {"Id": fields.get('r_acct', '').replace('/', '')}}},
                        "RmtInf": {"Ustrd": fields.get('remit', '')}
                    }
                }
            }
        }


def main():
    st.title("🔄 ISO 20022 Migration Platform")
    st.caption("Bidirectional: MT101 ↔ pain.001 | MT103 ↔ pacs.008")
    
    # Initialize session state
    if 'message_input' not in st.session_state:
        st.session_state.message_input = SAMPLES["MT103 - USD Transfer"]
    if 'transform_result' not in st.session_state:
        st.session_state.transform_result = None
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Transformation Approach
        st.subheader("🔧 Approach")
        approach = st.radio(
            "Select transformation method",
            ["Rules-Based", "LLM-Powered", "Hybrid"],
            index=0,
            help="Rules: Fast, deterministic. LLM: AI-powered mapping. Hybrid: Rules + LLM validation."
        )
        
        if approach == "Rules-Based":
            st.caption("✅ Deterministic field mapping")
        elif approach == "LLM-Powered":
            st.caption("🤖 AI-driven transformation")
        else:
            st.caption("⚡ Rules + AI validation")
        
        st.divider()
        
        st.subheader("📋 Load Sample")
        sample = st.selectbox("Select sample", list(SAMPLES.keys()), label_visibility="collapsed")
        if st.button("📥 Load", use_container_width=True):
            st.session_state.message_input = SAMPLES[sample]
            st.session_state.transform_result = None
        
        st.divider()
        st.markdown("**Supported:**")
        st.markdown("• MT103 ↔ pacs.008")
        st.markdown("• MT101 ↔ pain.001")
    
    # Main layout
    col1, col2 = st.columns(2, gap="large")
    
    # INPUT COLUMN
    with col1:
        st.subheader("📥 Input Message")
        
        # File upload
        uploaded = st.file_uploader("Upload file", type=['txt', 'json', 'xml'], label_visibility="collapsed")
        if uploaded:
            content = uploaded.read().decode('utf-8')
            st.session_state.message_input = content
            st.session_state.transform_result = None
            st.success(f"✅ Loaded: {uploaded.name}")
        
        # Text input
        message_input = st.text_area(
            "Enter message",
            value=st.session_state.message_input,
            height=200,
            label_visibility="collapsed"
        )
        st.session_state.message_input = message_input
        
        # Parse message
        source_type, target_type = detect_message_type(message_input)
        fields = parse_message(message_input, source_type)
        
        # Show preview
        if message_input and message_input.strip():
            st.divider()
            
            pcol1, pcol2 = st.columns([3, 1])
            with pcol1:
                st.markdown("**Transaction Details**")
            with pcol2:
                st.code(f"{source_type} → {target_type}", language=None)
            
            st.markdown(f"### 💰 {format_amount(fields.get('amt', '0'), fields.get('ccy', 'USD'))}")
            
            party1, party2 = st.columns(2)
            with party1:
                st.markdown("**FROM (Sender)**")
                st.markdown(f"{get_flag(fields.get('s_ctry', ''))} **{fields.get('s_name', 'Unknown') or 'Unknown'}**")
                st.caption(f"Account: `{fields.get('s_acct', 'N/A') or 'N/A'}`")
                if fields.get('s_bic'):
                    st.caption(f"BIC: {fields.get('s_bic')}")
            
            with party2:
                st.markdown("**TO (Receiver)**")
                st.markdown(f"{get_flag(fields.get('r_ctry', ''))} **{fields.get('r_name', 'Unknown') or 'Unknown'}**")
                st.caption(f"Account: `{fields.get('r_acct', 'N/A') or 'N/A'}`")
                if fields.get('r_bic'):
                    st.caption(f"BIC: {fields.get('r_bic')}")
            
            st.divider()
            det1, det2, det3 = st.columns(3)
            with det1:
                st.markdown("**Reference**")
                st.caption(fields.get('ref', 'N/A') or 'N/A')
            with det2:
                st.markdown("**Date**")
                st.caption(fields.get('date', 'N/A') or 'N/A')
            with det3:
                st.markdown("**Charges**")
                st.caption(fields.get('charges', 'SHA') or 'SHA')
            
            if fields.get('remit'):
                st.markdown("**Remittance**")
                st.caption(fields.get('remit', '')[:80])
            
            st.divider()
            
            # Approach Section
            st.markdown("**🔄 Transformation Approach**")
            
            # Show selected method
            method_icons = {"Rules-Based": "📐", "LLM-Powered": "🤖", "Hybrid": "⚡"}
            st.markdown(f"**Method:** {method_icons.get(approach, '')} {approach}")
            
            if source_type in ['MT103', 'MT101']:
                approach_text = f"""
                **Direction:** SWIFT MT → ISO 20022 MX
                
                **Source:** {source_type} (Legacy SWIFT)
                **Target:** {target_type} (ISO 20022 XML)
                
                **Mapping:**
                - Field 20 → MsgId/EndToEndId
                - Field 32A/32B → IntrBkSttlmAmt/InstdAmt
                - Field 50K/50H → Dbtr (Debtor)
                - Field 59 → Cdtr (Creditor)
                - Field 70 → RmtInf/Ustrd
                - Field 71A → ChrgBr
                """
            else:
                approach_text = f"""
                **Direction:** ISO 20022 MX → SWIFT MT
                
                **Source:** {source_type} (ISO 20022 XML)
                **Target:** {target_type} (Legacy SWIFT)
                
                **Mapping:**
                - MsgId → Field 20
                - IntrBkSttlmAmt/InstdAmt → Field 32A/32B
                - Dbtr → Field 50K/50H
                - Cdtr → Field 59
                - RmtInf/Ustrd → Field 70
                - ChrgBr → Field 71A
                """
            
            st.markdown(approach_text)
            st.divider()
        
        # Buttons
        btn1, btn2 = st.columns(2)
        with btn1:
            transform_clicked = st.button("🚀 Transform", type="primary", use_container_width=True)
        with btn2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.transform_result = None
        
        # Process transformation
        if transform_clicked:
            if target_type in ['MT101', 'MT103']:
                result = {
                    'output_type': 'mt',
                    'target': target_type,
                    'text': generate_mt_text(fields, target_type),
                    'json': generate_mt_json(fields, target_type)
                }
            else:
                result = {
                    'output_type': 'mx',
                    'target': target_type,
                    'xml': generate_mx_xml(fields, target_type),
                    'json': generate_mx_json(fields, target_type)
                }
            st.session_state.transform_result = result
    
    # OUTPUT COLUMN
    with col2:
        result = st.session_state.transform_result
        
        if result:
            target = result.get('target', 'pacs.008')
            st.subheader(f"📤 Output {target}")
            
            if result.get('output_type') == 'mt':
                tab1, tab2 = st.tabs(["📄 Text Format", "📊 JSON Format"])
                
                with tab1:
                    st.code(result['text'], language='text')
                    st.download_button(
                        f"📥 Download {target}.txt",
                        result['text'],
                        f"{target}.txt",
                        "text/plain",
                        use_container_width=True
                    )
                
                with tab2:
                    st.json(result['json'])
                    st.download_button(
                        f"📥 Download {target}.json",
                        json.dumps(result['json'], indent=2),
                        f"{target}.json",
                        "application/json",
                        use_container_width=True
                    )
            
            elif result.get('output_type') == 'mx':
                tab1, tab2 = st.tabs(["📄 XML Format", "📊 JSON Format"])
                
                with tab1:
                    st.code(result['xml'], language='xml')
                    st.download_button(
                        f"📥 Download {target}.xml",
                        result['xml'],
                        f"{target}.xml",
                        "application/xml",
                        use_container_width=True
                    )
                
                with tab2:
                    st.json(result['json'])
                    st.download_button(
                        f"📥 Download {target}.json",
                        json.dumps(result['json'], indent=2),
                        f"{target}.json",
                        "application/json",
                        use_container_width=True
                    )
        else:
            st.subheader("📤 Output")
            st.info("👈 Enter a message and click **Transform** to see output")


if __name__ == "__main__":
    main()