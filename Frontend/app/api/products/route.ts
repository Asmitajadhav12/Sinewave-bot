import { NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabaseServer";

export async function GET() {
  try {
    const supabaseClient = await createSupabaseServerClient();
    const { data, error } = await supabaseClient
      .from("products")
      .select("id, name: product_name")
      .order("product_name", { ascending: true });

    if (error) {
      console.error("PRODUCTS ERROR:", error);
      return NextResponse.json(
        { error: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(data ?? []);
  } catch (err: any) {
    console.error("UNEXPECTED ERROR:", err);
    return NextResponse.json(
      { error: "Unexpected server error" },
      { status: 500 }
    );
  }
}
