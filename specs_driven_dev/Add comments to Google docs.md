# Requirement for LLM to add comments to Google Docs via API

How can I add comments to Google Docs via API? If there's MCP server, it's even better.
I'm building an AI application that uses LLM to review Google Docs and make comments.

# Gemini answer

That's a great application for LLMs! You can absolutely add comments to Google Docs programmatically for your AI review application.

The primary method for managing comments on Google Docs is through the Google Drive API's comments resource.

1. Using the Google Drive API for Comments
The Google Docs content is managed by the Google Docs API, but the collaborative features like comments and replies are handled by the Google Drive API because they are associated with the file itself (a Drive resource), not the document's structure.

To create a new comment: You will use the create method on the comments resource in the Drive API (v3 is recommended).

You need to provide the fileId of the Google Doc.

The request body will contain the content of the comment.

Anchoring to Text: For your AI review, you will likely want to anchor the comment to a specific region of text. This is achieved by including an anchor property in the request body. This property is a JSON string that defines the revision ID (r) and the region (a) within the document. Defining the region for a text-anchored comment can be complex and requires understanding the document's structure and how ranges are defined.

2. LLM Integration with a Google Docs MCP Server
Since you specifically mentioned an MCP server (Modular Communication Protocol), this is an excellent and more streamlined path for an AI application. An MCP server acts as an agent/tool for your LLM, translating your natural language or structured output into API calls.

A community-driven, open-source Google Docs MCP Server exists (e.g., the one by a-bonus) that is designed to provide AI clients programmatic access to Google Docs and Drive features, including comment management (adding, reading, resolving comments).

Advantage for AI: This approach allows your LLM (like Claude or another compatible AI client) to interact with Google Docs using high-level commands, such as "Add a comment saying 'Grammar check suggested' to the second paragraph," instead of you having to manage the low-level API calls, authentication, and anchor calculation yourself.

If you choose the MCP Server route:

Set up a Google Cloud project, enable the Google Docs API and Google Drive API, and obtain OAuth 2.0 credentials (credentials.json).

Clone and set up the specific Google Docs MCP server repository.

Configure your AI client (where your LLM runs) to use this local MCP server endpoint.

This allows your LLM to handle the review logic, and then use the MCP tool's capabilities for comment creation, which abstracts the Drive API complexity.

Google Docs API: get document <https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/get>.
Google Drive API: add comments <https://developers.google.com/workspace/drive/api/guides/manage-comments>

# Question to Gemini

I will ask Claude Code to implement the integration to Google Docs API and Google Drive API. What's the best way to provide API specifications to Claude?

# Gemini's answer

That's a smart approach. To get the best results from **Claude Code**, you need to provide it with the API specifications in a **clear, structured, and goal-oriented format**.

Since the core task is creating an **anchored comment**, which involves two APIs, you need to be precise about which methods to use from each.

Here is the best way to structure the prompt and the specifications for Claude Code:

-----

## 1\. The High-Level Goal (The Prompt)

Start with a clear, concise instruction that defines the entire task, the language, and the output format you want.

> **Prompt Example:**
>
> "Generate a complete Python script using the `google-api-python-client` library to perform the following two-step process:
>
> 1. Retrieve the content and element IDs of a specific Google Doc using the Google Docs API.
> 2. Create an **anchored comment** on a specific text range within that document using the Google Drive API's `comments.create` method.
>
> The script must include functions for authentication, document reading, and comment creation. **Prioritize anchoring the comment to a specific paragraph of text (using `startIndex` and `endIndex` or similar range properties in the Docs API response structure).**"

## 2\. The Detailed API Specifications (The Data)

Provide the essential technical details as structured data (like a JSON or YAML object) or clear bullet points. Claude Code can interpret this better than just linking to documentation.

### A. Google Docs API (For Reading the Document Structure)

You need to read the document content to identify the exact position (indices) for the comment anchor.

* **API:** Google Docs API (v1)
* **Method:** `documents.get`
* **Purpose:** Read the document body to find the `startIndex` and `endIndex` of the text you want to comment on.
* **Request:**
  * `documentId`: The ID of the target file.
  * `fields`: Set to `body(content)` to minimize the payload.
* **Key Data Structure (Example Snippet):**

    ```json
    {
      "documentId": "...",
      "body": {
        "content": [
          {
            "startIndex": 1,
            "endIndex": 100,
            "paragraph": {
              "elements": [
                // Text runs you'd use to calculate character indices
              ]
            }
          }
        ]
      }
    }
    ```

### B. Google Drive API (For Creating the Comment)

This is the critical step for adding the comment.

* **API:** Google Drive API (v3)
* **Method:** `comments.create`
* **Endpoint:** `POST /drive/v3/files/{fileId}/comments`
* **Required Scopes:** `https://www.googleapis.com/auth/drive.file`
* **Request Body (Comment Resource):**
  * `content`: `string` (The actual comment text from your LLM.)
  * `anchor`: `string` (This must be a JSON string. This is the **most complex part** and requires specific attention from Claude Code.)

#### **The Anchor JSON Structure (Crucial Detail)**

For anchoring comments on a Google Doc, the `anchor` property needs to define the `revisionId` and the specific document region. The `anchor` field is a JSON string embedded within the main request JSON.

| Key | Type | Value/Description |
| :--- | :--- | :--- |
| **`r`** | `string` | The document's revision ID. Use **`head`** for the latest revision. |
| **`a`** | `array` | The list of regions the comment spans. |
| **`a[0].txt.o`** | `integer` | The starting offset (character index) of the text range. (Obtained from Docs API). |
| **`a[0].txt.l`** | `integer` | The length of the text range. |

**Example `anchor` JSON string:**

```json
"{\"r\": \"head\", \"a\": [{\"txt\": {\"o\": 10, \"l\": 45}}]}"
```

*(This anchors the comment to 45 characters of text starting at index 10 of the document's content.)*

-----

## 💡 Summary of Best Practices for Claude Code

1. **Use Markdown and Code Blocks:** Present the API structures and anchor format using code blocks and tables for maximum clarity.
2. **Specify the Client Library:** Explicitly state the programming language and the client library (`Python` and `google-api-python-client`).
3. **Define the Problem in Steps:** Break the complex task (read, calculate, write) into linear, easy-to-follow steps (e.g., Step 1: Get Content; Step 2: Calculate Anchor; Step 3: Create Comment).
4. **Provide a "Golden Example":** Include the exact structure for the most complex part (the `anchor` JSON string) to avoid ambiguity.

Would you like me to find the specific Python code examples for `comments.create` that include the `anchor` parameter from the Google documentation to add to your specification?

# Clarifications needed:

1. MCP vs Direct API: Do you want me to implement direct API integration, or would you prefer to use/configure an existing MCP
server?
2. Authentication: Do you already have Google Cloud credentials set up (credentials.json with OAuth 2.0), or do you need
guidance on that?
3. Project structure: Is this a new project, or should I integrate into the existing codebase in this directory? Would you like
me to explore the current project structure first?
4. LLM integration: How will the LLM decide what comments to make? Should I also implement the review logic, or just the API
integration for adding comments?