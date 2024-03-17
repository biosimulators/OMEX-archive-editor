"use client"


import Image from "next/image";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Tiptap } from "@/components/Tiptap";


export default function Home() {
  // perform validation on fields: TODO: use DOM Purifier for fields if saving to DB:
  const formSchema = z.object({
    title: z.string().min(5, {message: 'Title is not long enough'}),
    url: z.string().min(5, {message: 'This is neither a valid local archive path or hosted url.'}),
    description: z.string().max(100, {message: "That description is too large."}).trim(),
  });

  // keep track of changes and validation with each user change. Here we should take in the fields of an omex archive:
  const form = useForm<z.infer<typeof formSchema>>({
      resolver: zodResolver(formSchema),  // this acts as our extra validator on top of schema.
      mode: 'onChange',
      defaultValues: {
        title: 'Your OMEX/COMBINE ARCHIVE',
        url: 'Your URL here',
        description: 'Please upload the omex archive.'
    }

  });

  // handle submission (state change):
  function onSubmit(values: z.infer<typeof formSchema>) {
      // TODO: add SEDML validation and editing here.
      console.log(`THE SUBMIT: ${values.description}`);
  }


  return (
      <main className="p-24">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                    <FormItem>
                      <FormLabel>Title</FormLabel>
                      <FormControl>
                        <Input placeholder="Main title" {...field}/>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                )}
                />
              <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                      <FormItem>
                          <FormLabel>Description</FormLabel>
                          <FormControl>
                              <Tiptap description={field.name} onChange={field.onChange} />
                          </FormControl>
                          <FormMessage />
                      </FormItem>
                  )}
              />
          </form>
        </Form>
        <Button className="my-4" type={"submit"}>
            Submit
        </Button>
      </main>
  )
}






// import React, { useState } from 'react';
// import { useForm } from 'react-hook-form';
// import JSZip from 'jszip';
// import { saveAs } from 'file-saver';
// import RichTextEditor from '@/components/RichTextEditor';
//
// export default function Home() {
//   const [sedmlContent, setSedmlContent] = useState<string>('');
//
//   const form = useForm({
//     mode: 'onChange',
//   });
//
//   const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
//     const files = event.target.files;
//     if (files?.length) {
//       const zip = new JSZip();
//       try {
//         const content = await zip.loadAsync(files[0]);
//         // Assuming the SED-ML file is named 'model.sedml'
//         const sedmlFile = content.file('model.sedml');
//         if (sedmlFile) {
//           const sedmlText = await sedmlFile.async('text');
//           setSedmlContent(sedmlText);
//         }
//       } catch (error) {
//         console.error('Error reading the zip file: ', error);
//       }
//     }
//   };
//
//   const handleSave = () => {
//     const zip = new JSZip();
//     zip.file('model.sedml', sedmlContent);
//     zip.generateAsync({ type: 'blob' })
//         .then((content) => {
//           saveAs(content, 'archive.omex');
//         });
//   };
//
//   return (
//       <div>
//         <input type="file" accept=".omex" onChange={handleFileChange} />
//         <RichTextEditor content={sedmlContent} onChange={setSedmlContent} />
//         <button onClick={handleSave}>Export Archive</button>
//       </div>
//   );
// } */