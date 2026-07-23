import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { createSupabaseServerClient } from "@/lib/supabaseServer";

export const runtime = "nodejs";

const SCHEMA = process.env.SUPABASE_SCHEMA || "public";

/* ============================================================
   Upload Directory
============================================================ */
const ASSETS_DIR = path.resolve(
  process.env.ASSETS_DIR || path.join(process.cwd(), "assets")
);

// Ensure base upload folder exists
if (!fs.existsSync(ASSETS_DIR)) {
  fs.mkdirSync(ASSETS_DIR, { recursive: true });
}

/* ============================================================
   Auth Check
============================================================ */
const isUserAuthenticated = async (supabase: any) => {
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
  return new Response(
    JSON.stringify({ message: "Unauthorized" }),
    { status: 401 }
  );
}
};

/* ============================================================
   GET → Fetch errors
============================================================ */
export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const productId = searchParams.get("productId");
    const supabase = await createSupabaseServerClient();

    await isUserAuthenticated(supabase);

    let query = supabase
      .schema(SCHEMA)
      .from("error_knowledge_base")
      .select(`
        id,
        error_description,
        solution_steps,
        is_archived,
        product_id,
        function_area_id,
        function_area: function_area!error_knowledge_base_function_area_id_fkey (
          title
        ),
        error_screenshots (
          id,
          screenshot_url
        ),
        error_stats (
          id,
          is_resolved
      )
      `)
      .order("id", { ascending: false });

    if (productId && !isNaN(Number(productId))) {
      query = query.eq("product_id", Number(productId));
    }

    const { data, error } = await query;
    if (error) throw error;

    const formatted = (data ?? []).map((row: any) => {
      const stats = (row as any).error_stats || [];
      const totalReported = stats.length;
      const resolvedCount = stats.filter((s: any) => s.is_resolved).length;
      const notResolvedCount = totalReported - resolvedCount;

      return {

      id: String(row.id),
      description: row.error_description ?? "",
      solution: row.solution_steps ?? "",
      functionArea: row.function_area?.title ?? "",
      functionAreaId: row.function_area_id ?? null,
      archived: row.is_archived ?? false,
      productId: row.product_id ?? null,
      screenshots: row.error_screenshots ?? [],
      totalReported,
      resolvedCount,
      notResolvedCount,
    };
  });

    return NextResponse.json(formatted);
  } catch (err: any) {
    console.error("GET ERROR:", err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

/* ============================================================
   File Upload Helper
============================================================ */
async function handleFileUpload(
  errorId: number,
  files: File[],
  productTitle: string,
  supabaseClient: any
) {
  const screenshotIds: number[] = [];

  for (const file of files) {
    const buffer = Buffer.from(await file.arrayBuffer());
    const safeName = file.name.replace(/\s+/g, "_");
    const filename = `${Date.now()}-${safeName}`;

    // 🔥 Create product folder inside uploads/error-screenshots
    const productDir = path.join(ASSETS_DIR, productTitle);

    if (!fs.existsSync(productDir)) {
      fs.mkdirSync(productDir, { recursive: true });
    }

    const filePath = path.join(productDir, filename);

    fs.writeFileSync(filePath, buffer);

    // 🔥 Public URL
    const screenshotUrl = `${productTitle}/${filename}`;

    const { data, error } = await supabaseClient
      .schema(SCHEMA)
      .from("error_screenshots")
      .insert({
        error_id: errorId,
        screenshot_url: screenshotUrl,
      })
      .select("id")
      .single();

    if (!error && data) {
      screenshotIds.push(data.id);
    }
  }
  console.log(`Calling API: ${process.env.API_URL}/error/${errorId}/embeddings for snapshotIds ${screenshotIds}`);
  /*await fetch(`${process.env.API_URL}/error/${errorId}/embeddings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ screenshot_ids: screenshotIds }),
  });*/
  console.log("Embedding generated for screenshots:", screenshotIds);
}


/* ============================================================
   Delete Screenshots
============================================================ */
const deleteScreenshots = async (
  screenshotsToDelete: number[],
  supabaseClient: any
) => {
  const { data } = await supabaseClient
    .schema(SCHEMA)
    .from("error_screenshots")
    .delete()
    .in("id", screenshotsToDelete)
    .select("screenshot_url");

  await supabaseClient
    .schema(SCHEMA)
    .from("error_embeddings")
    .delete()
    .in("screenshot_id", screenshotsToDelete);

  data?.forEach((s: any) => {
    const filePath = path.join(ASSETS_DIR, s.screenshot_url);
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  });
};

/* ============================================================
   POST → Create Error
============================================================ */
export async function POST(req: Request) {
  try {
    const supabaseClient = await createSupabaseServerClient();
    await isUserAuthenticated(supabaseClient);

    const formData = await req.formData();
    const errorInfo = JSON.parse(formData.get("errorInfo") as string);
    const files = formData.getAll("screenshots") as File[];

    const {
      description,
      solution,
      functionAreaId,
      productId,
      productTitle,
    } = errorInfo;

    const { data, error } = await supabaseClient
      .schema(SCHEMA)
      .from("error_knowledge_base")
      .insert({
        error_description: description,
        solution_steps: solution,
        function_area_id: Number(functionAreaId),
        product_id: Number(productId),
        is_archived: false,
        created_at: new Date().toISOString(),
      })
      .select("id")
      .single();

    if (error) throw error;

    const errorId = data.id;

    if (files.length > 0) {
      await handleFileUpload(errorId, files, productTitle, supabaseClient);
    }

    return NextResponse.json({ success: true });
  } catch (err: any) {
    console.error("POST ERROR:", err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

/* ============================================================
   PUT → Archive OR Edit
============================================================ */
export async function PUT(req: Request) {
  try {
    const supabaseClient = await createSupabaseServerClient();
    await isUserAuthenticated(supabaseClient);

    /* ===== Edit (FormData) ===== */
    const formData = await req.formData();
    const errorInfo = JSON.parse(formData.get("errorInfo") as string);
    const files = formData.getAll("screenshots") as File[];
    const screenshotsToDeleteRaw = formData.get("screenshotsToDelete");

    const screenshotsToDelete = screenshotsToDeleteRaw
      ? JSON.parse(screenshotsToDeleteRaw as string)
      : [];

    const {
      errorId,
      description,
      solution,
      functionAreaId,
      productTitle,
    } = errorInfo;

    const { error } = await supabaseClient
      .schema(SCHEMA)
      .from("error_knowledge_base")
      .update({
        error_description: description,
        solution_steps: solution,
        function_area_id: Number(functionAreaId),
        updated_at: new Date().toISOString(),
      })
      .eq("id", Number(errorId));

    if (error) throw error;

    if (screenshotsToDelete.length > 0) {
      await deleteScreenshots(screenshotsToDelete, supabaseClient);
    }

    if (files.length > 0) {
      await handleFileUpload(Number(errorId), files, productTitle, supabaseClient);
    }

    return NextResponse.json({ success: true });
  } catch (err: any) {
    console.error("PUT ERROR:", err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
/* ============================================================
   PATCH → Archive / Unarchive Error
============================================================ */
export async function PATCH(req: Request) {
  try {
    const supabaseClient = await createSupabaseServerClient();
    await isUserAuthenticated(supabaseClient);

    const body = await req.json();
    const { id, archived } = body;

    if (!id) {
      return NextResponse.json(
        { error: "Error ID is required" },
        { status: 400 }
      );
    }

    const { error } = await supabaseClient
      .schema(SCHEMA)
      .from("error_knowledge_base")
      .update({ is_archived: archived })
      .eq("id", Number(id));

    if (error) throw error;

    return NextResponse.json({ success: true });

  } catch (err: any) {
    console.error("PATCH ERROR:", err);
    return NextResponse.json(
      { error: err.message },
      { status: 500 }
    );
  }
}

/* ============================================================
   DELETE
============================================================ */
export async function DELETE(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const id = Number(searchParams.get("id"));

    const supabaseClient = await createSupabaseServerClient();
    await isUserAuthenticated(supabaseClient);

    const { data } = await supabaseClient
      .schema(SCHEMA)
      .from("error_screenshots")
      .select("id")
      .eq("error_id", id);

    if (data?.length) {
      await deleteScreenshots(data.map((s: any) => s.id), supabaseClient);
    }

    await supabaseClient
      .schema(SCHEMA)
      .from("error_embeddings")
      .delete()
      .eq("error_info_id", id);

    await supabaseClient
      .schema(SCHEMA)
      .from("error_knowledge_base")
      .delete()
      .eq("id", id);

    return NextResponse.json({ success: true });
  } catch (err: any) {
    console.error("DELETE ERROR:", err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
