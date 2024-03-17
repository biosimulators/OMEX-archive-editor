import React from 'react';

interface RichTextEditorProps {
    content: string;
    onChange: (newContent: string) => void;
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({ content, onChange }) => {
    // Implement the XML editor component here.
    // Use the content prop as the initial value of the editor.
    // Use the onChange prop to notify the parent component of content changes.

    return <textarea value={content} onChange={(e) => onChange(e.target.value)} />;
};

export default RichTextEditor;