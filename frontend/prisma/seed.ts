import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  const count = await prisma.validationRule.count();
  if (count > 0) {
    console.log("Rules already seeded");
    return;
  }

  await prisma.validationRule.createMany({
    data: [
      { countryName: "India", countryCode: "+91", fieldName: "phone", validationType: "phone_length", ruleValue: "10" },
      { countryName: "Singapore", countryCode: "+65", fieldName: "phone", validationType: "phone_length", ruleValue: "8" },
      { countryName: "Global", countryCode: "", fieldName: "email", validationType: "email_format", ruleValue: "standard" },
      { countryName: "Global", countryCode: "", fieldName: "payment_method", validationType: "enum", ruleValue: "UPI,Card,Wallet,Net Banking,Cash" },
    ],
  });
  console.log("Seeded default validation rules");
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
