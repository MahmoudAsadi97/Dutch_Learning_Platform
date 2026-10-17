import { redirect } from "next/navigation";

/** Old bookmarks lead to the narrated story library; video creation has been retired. */
export default function RetiredVideoPage() {
  redirect("/verhalen");
}
