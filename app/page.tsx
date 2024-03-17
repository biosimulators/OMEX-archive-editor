import Image from "next/image";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from "@/components/ui/form";
import { useForm } from "react-hook-form";
import * as z from "zod";

export default function Home() {
  // keep track of changes and validation. Here we should take in the fields of an omex archive.
  const form = useForm({
    mode: 'onChange',

  });
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