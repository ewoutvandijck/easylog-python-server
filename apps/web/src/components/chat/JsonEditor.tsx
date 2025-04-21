'use client';

import Editor, { BeforeMount } from '@monaco-editor/react';

export interface ToolJsonEditorProps {
  value: string;
  onChange: (value: string) => void;
}

const ToolJsonEditor = ({ value, onChange }: ToolJsonEditorProps) => {
  const handleEditorBeforeMount: BeforeMount = (monaco) => {
    monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
      validate: true,
      schemas: [
        {
          uri: 'https://json-schema.org/draft/2020-12/schema',
          fileMatch: ['*'],
          schema: {
            $schema: 'http://json-schema.org/draft-07/schema#',
            oneOf: [
              {
                type: 'object',
                required: ['agent_class'],
                properties: {
                  agent_class: {
                    type: 'string',
                    description: 'The class name of the agent'
                  }
                },
                additionalProperties: true
              }
            ]
          }
        }
      ]
    });
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value) {
      onChange(value);
    }
  };

  return (
    <div className="h-[500px] w-full">
      <Editor
        className="rounded-md border border-input bg-transparent shadow-sm overflow-hidden"
        height="100%"
        defaultLanguage="json"
        defaultValue={value}
        beforeMount={handleEditorBeforeMount}
        onChange={handleEditorChange}
        options={{
          minimap: { enabled: false },
          language: 'json',
          formatOnPaste: true,
          formatOnType: true,
          automaticLayout: true,
          tabSize: 2,
          fontSize: 14,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          wrappingIndent: 'indent',
          folding: true,
          lineNumbers: 'on',
          glyphMargin: false,
          trimAutoWhitespace: true
        }}
        theme="vs-light"
      />
    </div>
  );
};

export default ToolJsonEditor;
