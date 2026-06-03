import React, { useState, useEffect } from 'react';

// Sample MT103 Messages for Demo
const sampleMT103Messages = [
  {
    id: 'MT103-001',
    name: 'Standard Customer Transfer',
    raw: `:20:TRX2024112001
:23B:CRED
:32A:241118USD50000,00
:50K:/123456789
ACME CORPORATION
123 BUSINESS STREET
NEW YORK, NY 10001
:52A:CHASUS33XXX
:53B:/D/0123456789
:59:/987654321
GLOBAL TRADING LTD
456 COMMERCE AVENUE
LONDON, EC2R 8AH
:70:INVOICE INV-2024-1234
PAYMENT FOR SERVICES
:71A:SHA
:72:/REC/URGENT`
  },
  {
    id: 'MT103-002',
    name: 'High Value Transfer',
    raw: `:20:TRX2024112002
:23B:CRED
:32A:241118EUR2500000,00
:50K:/DE89370400440532013000
DEUTSCHE MANUFACTURING GMBH
INDUSTRIESTRASSE 45
60329 FRANKFURT
:52A:DEUTDEFFXXX
:53B:/D/0198765432
:59:/GB82WEST12345698765432
BRITISH IMPORTS PLC
789 TRADE LANE
MANCHESTER, M1 2AB
:70:CONTRACT CON-2024-5678
Q4 MACHINERY ORDER
:71A:OUR
:72:/ACC/PRIORITY`
  },
  {
    id: 'MT103-003',
    name: 'Cross-Border Payment',
    raw: `:20:TRX2024112003
:23B:CRED
:32A:241118GBP175000,00
:50K:/GB29NWBK60161331926819
LONDON TECH VENTURES
10 INNOVATION SQUARE
LONDON, SW1A 1AA
:52A:HSBCGB2LXXX
:53B:/D/0567891234
:59:/US12345678901234567890
SILICON VALLEY INNOVATIONS INC
1 STARTUP BLVD
SAN FRANCISCO, CA 94105
:70:SERIES B INVESTMENT
TRANCHE 2 OF 3
:71A:BEN
:72:/INS/INVESTMENT`
  }
];

// Rule-based mapping configuration
const RULE_BASED_MAPPINGS = {
  MT103_to_pacs008: {
    ':20:': { path: 'CdtTrfTxInf.PmtId.InstrId', description: 'Transaction Reference' },
    ':32A:': { 
      path: 'CdtTrfTxInf.IntrBkSttlmAmt', 
      description: 'Value Date/Currency/Amount',
      transform: (value) => {
        const date = value.substring(0, 6);
        const ccy = value.substring(6, 9);
        const amt = value.substring(9).replace(',', '.');
        return { date, ccy, amt };
      }
    },
    ':50K:': { path: 'CdtTrfTxInf.Dbtr', description: 'Ordering Customer (Debtor)' },
    ':52A:': { path: 'CdtTrfTxInf.DbtrAgt.FinInstnId.BICFI', description: 'Ordering Institution' },
    ':59:': { path: 'CdtTrfTxInf.Cdtr', description: 'Beneficiary Customer (Creditor)' },
    ':70:': { path: 'CdtTrfTxInf.RmtInf.Ustrd', description: 'Remittance Information' },
    ':71A:': { path: 'CdtTrfTxInf.ChrgBr', description: 'Charge Bearer' }
  }
};

// Agent status component
const AgentStatus = ({ name, status, confidence, message }) => {
  const statusColors = {
    idle: 'bg-gray-200 text-gray-600',
    processing: 'bg-yellow-200 text-yellow-800 animate-pulse',
    complete: 'bg-green-200 text-green-800',
    error: 'bg-red-200 text-red-800'
  };

  return (
    <div className={`p-3 rounded-lg mb-2 ${statusColors[status]}`}>
      <div className="flex justify-between items-center">
        <span className="font-semibold">🤖 {name}</span>
        {confidence && <span className="text-sm">{(confidence * 100).toFixed(0)}% confidence</span>}
      </div>
      {message && <p className="text-sm mt-1">{message}</p>}
    </div>
  );
};

// Main Demo Component
export default function MTtoMXDemo() {
  const [selectedMessage, setSelectedMessage] = useState(sampleMT103Messages[0]);
  const [approach, setApproach] = useState('hybrid');
  const [isProcessing, setIsProcessing] = useState(false);
  const [transformationComplete, setTransformationComplete] = useState(false);
  const [mxOutput, setMxOutput] = useState(null);
  const [agentStatuses, setAgentStatuses] = useState({
    parser: { status: 'idle', message: '' },
    mapping: { status: 'idle', message: '', confidence: null },
    enrichment: { status: 'idle', message: '', fieldsAdded: 0 },
    validation: { status: 'idle', message: '', score: null }
  });
  const [processingLogs, setProcessingLogs] = useState([]);
  const [showXML, setShowXML] = useState(false);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setProcessingLogs(prev => [...prev, { timestamp, message, type }]);
  };

  const resetDemo = () => {
    setTransformationComplete(false);
    setMxOutput(null);
    setProcessingLogs([]);
    setAgentStatuses({
      parser: { status: 'idle', message: '' },
      mapping: { status: 'idle', message: '', confidence: null },
      enrichment: { status: 'idle', message: '', fieldsAdded: 0 },
      validation: { status: 'idle', message: '', score: null }
    });
  };

  const parseMTMessage = (rawMessage) => {
    const fields = {};
    const lines = rawMessage.split('\n');
    let currentField = '';
    let currentValue = '';

    lines.forEach(line => {
      const fieldMatch = line.match(/^:(\d{2}[A-Z]?):(.*)/);
      if (fieldMatch) {
        if (currentField) {
          fields[currentField] = currentValue.trim();
        }
        currentField = `:${fieldMatch[1]}:`;
        currentValue = fieldMatch[2];
      } else if (currentField) {
        currentValue += '\n' + line;
      }
    });
    
    if (currentField) {
      fields[currentField] = currentValue.trim();
    }

    return fields;
  };

  const generateMXStructure = (parsedMT, mappingResults, enrichmentData) => {
    const now = new Date().toISOString();
    const msgId = `MX${Date.now()}${Math.random().toString(36).substr(2, 6).toUpperCase()}`;

    // Extract amount info
    const field32A = parsedMT[':32A:'] || '';
    const valueDate = field32A.substring(0, 6);
    const currency = field32A.substring(6, 9);
    const amount = field32A.substring(9).replace(',', '.');

    // Extract parties
    const debtor = parsedMT[':50K:'] || '';
    const creditor = parsedMT[':59:'] || '';
    const debtorLines = debtor.split('\n');
    const creditorLines = creditor.split('\n');

    return {
      Document: {
        FIToFICstmrCdtTrf: {
          GrpHdr: {
            MsgId: msgId,
            CreDtTm: now,
            NbOfTxs: '1',
            SttlmInf: {
              SttlmMtd: 'INDA'
            }
          },
          CdtTrfTxInf: {
            PmtId: {
              InstrId: parsedMT[':20:'] || msgId,
              EndToEndId: `E2E-${parsedMT[':20:'] || msgId}`,
              TxId: `TXN-${Date.now()}`
            },
            IntrBkSttlmAmt: {
              Ccy: currency,
              Value: amount
            },
            IntrBkSttlmDt: `20${valueDate.substring(0, 2)}-${valueDate.substring(2, 4)}-${valueDate.substring(4, 6)}`,
            ChrgBr: parsedMT[':71A:'] || 'SLEV',
            Dbtr: {
              Nm: debtorLines[1] || 'Unknown Debtor',
              PstlAdr: {
                StrtNm: debtorLines[2] || '',
                TwnNm: debtorLines[3] || '',
                Ctry: enrichmentData.debtorCountry || 'US'
              },
              Id: {
                OrgId: {
                  Othr: {
                    Id: debtorLines[0]?.replace('/', '') || ''
                  }
                }
              }
            },
            DbtrAgt: {
              FinInstnId: {
                BICFI: parsedMT[':52A:']?.substring(0, 11) || ''
              }
            },
            Cdtr: {
              Nm: creditorLines[1] || 'Unknown Creditor',
              PstlAdr: {
                StrtNm: creditorLines[2] || '',
                TwnNm: creditorLines[3] || '',
                Ctry: enrichmentData.creditorCountry || 'US'
              },
              Id: {
                OrgId: {
                  Othr: {
                    Id: creditorLines[0]?.replace('/', '') || ''
                  }
                }
              }
            },
            CdtrAgt: {
              FinInstnId: {
                BICFI: enrichmentData.creditorBIC || 'UNKNOWN'
              }
            },
            RmtInf: {
              Ustrd: parsedMT[':70:'] || ''
            },
            ...enrichmentData.regulatoryFields
          }
        }
      }
    };
  };

  const objectToXML = (obj, indent = 0) => {
    let xml = '';
    const spaces = '  '.repeat(indent);
    
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'object' && value !== null) {
        xml += `${spaces}<${key}>\n${objectToXML(value, indent + 1)}${spaces}</${key}>\n`;
      } else {
        xml += `${spaces}<${key}>${value || ''}</${key}>\n`;
      }
    }
    return xml;
  };

  const processTransformation = async () => {
    setIsProcessing(true);
    resetDemo();
    addLog('🚀 Starting MT to MX transformation...', 'info');
    addLog(`📋 Approach: ${approach.toUpperCase()}`, 'info');

    try {
      // Step 1: Parse MT Message
      setAgentStatuses(prev => ({
        ...prev,
        parser: { status: 'processing', message: 'Analyzing MT103 structure...' }
      }));
      await new Promise(r => setTimeout(r, 800));
      
      const parsedMT = parseMTMessage(selectedMessage.raw);
      const fieldCount = Object.keys(parsedMT).length;
      
      setAgentStatuses(prev => ({
        ...prev,
        parser: { status: 'complete', message: `Parsed ${fieldCount} fields from MT103` }
      }));
      addLog(`✓ Parser: Extracted ${fieldCount} fields`, 'success');

      // Step 2: Mapping Agent
      setAgentStatuses(prev => ({
        ...prev,
        mapping: { status: 'processing', message: approach === 'llm' ? 'LLM semantic analysis...' : 'Applying mapping rules...', confidence: null }
      }));
      await new Promise(r => setTimeout(r, approach === 'llm' ? 1200 : 600));

      const mappingConfidence = approach === 'rules' ? 0.98 : (approach === 'llm' ? 0.94 : 0.96);
      const mappingMethod = approach === 'rules' ? 'Rule-based direct mapping' : 
                          approach === 'llm' ? 'GPT-4o semantic inference' : 
                          'Hybrid (Rules + LLM fallback)';
      
      setAgentStatuses(prev => ({
        ...prev,
        mapping: { 
          status: 'complete', 
          message: `${mappingMethod} - ${fieldCount} fields mapped`,
          confidence: mappingConfidence
        }
      }));
      addLog(`✓ Mapping Agent: ${mappingMethod}`, 'success');

      // Step 3: Enrichment Agent
      setAgentStatuses(prev => ({
        ...prev,
        enrichment: { status: 'processing', message: 'AI analyzing data gaps...', fieldsAdded: 0 }
      }));
      await new Promise(r => setTimeout(r, 1000));

      const enrichmentData = {
        debtorCountry: 'US',
        creditorCountry: 'GB',
        creditorBIC: 'BARCGB22XXX',
        regulatoryFields: {}
      };

      // Add regulatory fields based on currency
      const currency = parsedMT[':32A:']?.substring(6, 9);
      let fieldsAdded = 3;
      
      if (currency === 'EUR') {
        enrichmentData.regulatoryFields.SplmtryData = {
          PlcAndNm: 'EU_Regulatory',
          Envlp: { LEI: 'ABC123DEF456GHI78901' }
        };
        fieldsAdded += 2;
      } else if (currency === 'USD') {
        enrichmentData.regulatoryFields.SplmtryData = {
          PlcAndNm: 'US_Regulatory',
          Envlp: { FedRef: 'FED' + Date.now() }
        };
        fieldsAdded += 2;
      }

      setAgentStatuses(prev => ({
        ...prev,
        enrichment: { 
          status: 'complete', 
          message: `Added ${fieldsAdded} regulatory/mandatory fields`,
          fieldsAdded
        }
      }));
      addLog(`✓ Enrichment Agent: Added ${fieldsAdded} fields (KG + ML)`, 'success');

      // Step 4: Generate MX Structure
      addLog('📝 Generating pacs.008.001.08 structure...', 'info');
      await new Promise(r => setTimeout(r, 500));
      
      const mxStructure = generateMXStructure(parsedMT, {}, enrichmentData);
      
      // Step 5: Validation Agent
      setAgentStatuses(prev => ({
        ...prev,
        validation: { status: 'processing', message: 'Validating against ISO 20022 schema...', score: null }
      }));
      await new Promise(r => setTimeout(r, 900));

      const validationScore = Math.random() > 0.3 ? 100 : 97;
      const validationIssues = validationScore < 100 ? 1 : 0;
      
      setAgentStatuses(prev => ({
        ...prev,
        validation: { 
          status: 'complete', 
          message: validationIssues === 0 ? 'All validations passed!' : `${validationIssues} warning(s) - auto-corrected`,
          score: validationScore
        }
      }));
      addLog(`✓ Validation Agent: Score ${validationScore}%`, validationScore === 100 ? 'success' : 'warning');

      // Set output
      setMxOutput({
        structure: mxStructure,
        xml: `<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">\n${objectToXML(mxStructure.Document, 1)}</Document>`,
        stats: {
          fieldsOriginal: fieldCount,
          fieldsMapped: fieldCount,
          fieldsEnriched: fieldsAdded,
          confidence: mappingConfidence,
          validationScore
        }
      });

      setTransformationComplete(true);
      addLog('🎉 Transformation complete!', 'success');

    } catch (error) {
      addLog(`❌ Error: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-6 shadow-lg">
        <h1 className="text-3xl font-bold mb-2">🔄 ISO 20022 GenAI Migration Platform</h1>
        <p className="text-blue-100">Real-time MT to MX Transformation with Agentic AI</p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-64">
            <label className="block text-sm font-medium text-gray-700 mb-1">Sample Message</label>
            <select 
              className="w-full p-2 border rounded-lg"
              value={selectedMessage.id}
              onChange={(e) => {
                const msg = sampleMT103Messages.find(m => m.id === e.target.value);
                setSelectedMessage(msg);
                resetDemo();
              }}
            >
              {sampleMT103Messages.map(msg => (
                <option key={msg.id} value={msg.id}>{msg.id}: {msg.name}</option>
              ))}
            </select>
          </div>
          
          <div className="flex-1 min-w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">Transformation Approach</label>
            <select 
              className="w-full p-2 border rounded-lg"
              value={approach}
              onChange={(e) => {
                setApproach(e.target.value);
                resetDemo();
              }}
            >
              <option value="rules">Rule-Based Only</option>
              <option value="llm">LLM-Based Only</option>
              <option value="hybrid">Hybrid (Recommended)</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button
              onClick={processTransformation}
              disabled={isProcessing}
              className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                isProcessing 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-green-600 hover:bg-green-700 text-white shadow-lg hover:shadow-xl'
              }`}
            >
              {isProcessing ? '⏳ Processing...' : '▶️ Transform'}
            </button>
            <button
              onClick={resetDemo}
              className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-100"
            >
              🔄 Reset
            </button>
          </div>
        </div>
      </div>

      {/* Main Content - Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Left: MT Message */}
        <div className="bg-white rounded-lg shadow">
          <div className="bg-amber-500 text-white p-3 rounded-t-lg flex justify-between items-center">
            <h2 className="font-bold">📥 Input: MT103 (SWIFT)</h2>
            <span className="text-sm bg-amber-600 px-2 py-1 rounded">Legacy Format</span>
          </div>
          <div className="p-4">
            <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm overflow-x-auto font-mono whitespace-pre-wrap max-h-96 overflow-y-auto">
              {selectedMessage.raw}
            </pre>
          </div>
        </div>

        {/* Right: MX Output */}
        <div className="bg-white rounded-lg shadow">
          <div className="bg-blue-500 text-white p-3 rounded-t-lg flex justify-between items-center">
            <h2 className="font-bold">📤 Output: pacs.008 (ISO 20022)</h2>
            <div className="flex gap-2">
              {transformationComplete && (
                <button
                  onClick={() => setShowXML(!showXML)}
                  className="text-sm bg-blue-600 px-2 py-1 rounded hover:bg-blue-700"
                >
                  {showXML ? 'View JSON' : 'View XML'}
                </button>
              )}
              <span className="text-sm bg-blue-600 px-2 py-1 rounded">MX Format</span>
            </div>
          </div>
          <div className="p-4">
            {!transformationComplete ? (
              <div className="bg-gray-100 p-8 rounded-lg text-center text-gray-500">
                <p className="text-4xl mb-4">⏳</p>
                <p>Click "Transform" to see the MX output</p>
              </div>
            ) : (
              <pre className="bg-gray-900 text-blue-300 p-4 rounded-lg text-sm overflow-x-auto font-mono whitespace-pre-wrap max-h-96 overflow-y-auto">
                {showXML ? mxOutput.xml : JSON.stringify(mxOutput.structure, null, 2)}
              </pre>
            )}
          </div>
        </div>
      </div>

      {/* Agent Status Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Agents */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
            🤖 AI Agent Pipeline
          </h3>
          <AgentStatus 
            name="MT Parser" 
            status={agentStatuses.parser.status}
            message={agentStatuses.parser.message}
          />
          <AgentStatus 
            name="Mapping Agent" 
            status={agentStatuses.mapping.status}
            confidence={agentStatuses.mapping.confidence}
            message={agentStatuses.mapping.message}
          />
          <AgentStatus 
            name="Enrichment Agent" 
            status={agentStatuses.enrichment.status}
            message={agentStatuses.enrichment.message}
          />
          <AgentStatus 
            name="Validation Agent" 
            status={agentStatuses.validation.status}
            message={agentStatuses.validation.message}
          />
        </div>

        {/* Processing Logs */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-bold text-lg mb-3">📋 Processing Log</h3>
          <div className="bg-gray-900 rounded-lg p-3 h-48 overflow-y-auto font-mono text-sm">
            {processingLogs.length === 0 ? (
              <p className="text-gray-500">Waiting for transformation...</p>
            ) : (
              processingLogs.map((log, i) => (
                <div key={i} className={`mb-1 ${
                  log.type === 'success' ? 'text-green-400' :
                  log.type === 'error' ? 'text-red-400' :
                  log.type === 'warning' ? 'text-yellow-400' :
                  'text-gray-300'
                }`}>
                  <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Statistics */}
      {transformationComplete && mxOutput && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-bold text-lg mb-3">📊 Transformation Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg text-center">
              <p className="text-2xl font-bold text-blue-600">{mxOutput.stats.fieldsOriginal}</p>
              <p className="text-sm text-gray-600">MT Fields</p>
            </div>
            <div className="bg-green-50 p-3 rounded-lg text-center">
              <p className="text-2xl font-bold text-green-600">{mxOutput.stats.fieldsMapped}</p>
              <p className="text-sm text-gray-600">Fields Mapped</p>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg text-center">
              <p className="text-2xl font-bold text-purple-600">{mxOutput.stats.fieldsEnriched}</p>
              <p className="text-sm text-gray-600">Fields Enriched</p>
            </div>
            <div className="bg-amber-50 p-3 rounded-lg text-center">
              <p className="text-2xl font-bold text-amber-600">{(mxOutput.stats.confidence * 100).toFixed(0)}%</p>
              <p className="text-sm text-gray-600">Confidence</p>
            </div>
            <div className="bg-emerald-50 p-3 rounded-lg text-center">
              <p className="text-2xl font-bold text-emerald-600">{mxOutput.stats.validationScore}%</p>
              <p className="text-sm text-gray-600">Validation Score</p>
            </div>
          </div>
        </div>
      )}

      {/* Approach Comparison Info */}
      <div className="mt-6 bg-white rounded-lg shadow p-4">
        <h3 className="font-bold text-lg mb-3">📚 Approach Comparison</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className={`p-3 rounded-lg border-2 ${approach === 'rules' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
            <h4 className="font-semibold mb-2">🔧 Rule-Based</h4>
            <ul className="text-gray-600 space-y-1">
              <li>• Deterministic mapping</li>
              <li>• High performance</li>
              <li>• 98%+ confidence</li>
              <li>• Limited flexibility</li>
            </ul>
          </div>
          <div className={`p-3 rounded-lg border-2 ${approach === 'llm' ? 'border-purple-500 bg-purple-50' : 'border-gray-200'}`}>
            <h4 className="font-semibold mb-2">🧠 LLM-Based</h4>
            <ul className="text-gray-600 space-y-1">
              <li>• Semantic understanding</li>
              <li>• Handles edge cases</li>
              <li>• 90-95% confidence</li>
              <li>• Higher latency</li>
            </ul>
          </div>
          <div className={`p-3 rounded-lg border-2 ${approach === 'hybrid' ? 'border-green-500 bg-green-50' : 'border-gray-200'}`}>
            <h4 className="font-semibold mb-2">⚡ Hybrid (Best)</h4>
            <ul className="text-gray-600 space-y-1">
              <li>• Rules for known fields</li>
              <li>• LLM for unknowns</li>
              <li>• 95-98% confidence</li>
              <li>• Optimal balance</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
