"use client"

// Parse and render message content with proper bullet point formatting
function renderMessageContent(content: string) {
  // Split content by bullet points
  const parts = content.split(/\s*•\s+/)

  if (parts.length === 1) {
    // No bullets found, return as-is
    return <span>{content}</span>
  }

  // First part is the intro text before bullets
  const intro = parts[0].trim()
  const bullets = parts.slice(1).filter(b => b.trim().length > 0)

  return (
    <div>
      {intro && <div className="mb-3">{intro}</div>}
      {bullets.length > 0 && (
        <ul className="list-none space-y-2 pl-0">
          {bullets.map((bullet, index) => (
            <li key={index} className="flex items-start">
              <span className="mr-2 mt-1 flex-shrink-0">•</span>
              <span className="flex-1">{bullet.trim()}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function TestBullets() {
  const testCases = [
    {
      title: "Your Actual Case - Escalate Directly",
      text: "Recommend escalating directly to CEO without re-negotiation. • Customer has high acceptance rate (5 accepted deviations across 3 contracts = 67% flexibility rate) • All three violation types in this contract were previously accepted by us for this customer • Low negotiation rounds (1.3 avg) indicates cooperative relationship • Historical pattern strongly suggests internal approval is likely despite high escalation level"
    },
    {
      title: "Re-Negotiate Case",
      text: "Recommend re-negotiating before escalation. • Zero accepted deviations with this customer (0/3 contracts) indicates we maintain strict policies with Zeus Fiction Oy • High negotiation rounds (6.3 avg) shows historically difficult relationship and protracted negotiations • Current violations are severe (500% liability cap, 20% daily penalties) and unlikely to be approved internally given our historical stance • Re-negotiation to reduce violations will save executive time and increase approval likelihood"
    },
    {
      title: "Simple Test",
      text: "This is a test. • First bullet • Second bullet • Third bullet"
    },
    {
      title: "No Bullets",
      text: "This is just regular text without any bullets."
    }
  ]

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Bullet Point Formatting Test</h1>

      <div className="space-y-6">
        {testCases.map((testCase, index) => (
          <div key={index} className="border rounded-lg p-6 bg-white shadow-sm">
            <h2 className="text-xl font-semibold mb-3 text-blue-600">{testCase.title}</h2>

            <div className="mb-4">
              <div className="text-sm font-medium text-gray-600 mb-2">Raw Input:</div>
              <div className="bg-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
                {testCase.text}
              </div>
            </div>

            <div>
              <div className="text-sm font-medium text-gray-600 mb-2">Formatted Output:</div>
              <div className="bg-gray-50 p-4 rounded border-l-4 border-green-500">
                {renderMessageContent(testCase.text)}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold mb-2">How It Works:</h3>
        <ul className="list-disc list-inside space-y-1 text-sm">
          <li>Splits text by bullet character (•)</li>
          <li>First part becomes intro text</li>
          <li>Each bullet becomes a list item with proper spacing</li>
          <li>Uses flexbox to ensure bullets stay aligned</li>
          <li>No dependency on LLM adding newlines</li>
        </ul>
      </div>
    </div>
  )
}
