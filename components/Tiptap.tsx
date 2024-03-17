"use client"
import { useEditor, EditorContent } from "@tiptap/react";
import {StarterKit} from "@tiptap/starter-kit";

export default function Tiptap({
    description,
    onChange
}: {
    description: string
    onChange: (richText: string) => void
}) {
    const editor = useEditor({
        extensions: [StarterKit.configure()],
        content: description,
        editorProps: {
            attributes: {
                class:
                    "rounded-md border min-h-[150px] border-input bg-black"
            },
        },
        onUpdate({editor}) {
            onChange(editor.getHTML())
            console.log(`THE EDITOR HTML: ${editor.getHTML()}`)
        },
    })

    return (
        <div className={"flex flex-col justify-stretch min-h-[250px]"}>
            <EditorContent editor={editor}/>
        </div>
    )
}

export { Tiptap };