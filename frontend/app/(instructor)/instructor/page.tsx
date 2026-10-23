import { redirect } from "next/navigation";

export default function InstructorIndex() {
  redirect("/instructor/courses");
}
