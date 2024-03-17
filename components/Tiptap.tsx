"use client"
import { useEditor, EditorContent } from "@tiptap/react";
import { StarterKit } from "@tiptap/starter-kit";
import { ToolBar } from "@/components/ToolBar";

export default function TipTap({
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
            <ToolBar editor={editor} />
            <EditorContent editor={editor}/>
        </div>
    )
}

export { TipTap };