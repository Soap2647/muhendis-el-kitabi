# -*- coding: utf-8 -*-
"""b40_5b_capraz.py: Elle kodlamayi resmi kutuphaneyle karsilastirir.

protoc calismiyor olabilir; bunun yerine tanimi FileDescriptorProto
ile programatik olarak kurup google.protobuf'a verir.
"""
from google.protobuf import descriptor_pb2, descriptor_pool
from google.protobuf.message_factory import GetMessageClass

import b40_5_protobuf as el

F = descriptor_pb2.FieldDescriptorProto
fdp = descriptor_pb2.FileDescriptorProto(
    name="telemetri.proto", package="b40", syntax="proto3")
mesaj = fdp.message_type.add(name="Telemetri")
for ad, no, tip in (("id", 1, F.TYPE_UINT32),
                    ("sicaklik", 2, F.TYPE_SINT32),
                    ("ad", 4, F.TYPE_STRING)):
    mesaj.field.add(name=ad, number=no, type=tip,
                    label=F.LABEL_OPTIONAL)

havuz = descriptor_pool.DescriptorPool()
havuz.AddSerializedFile(fdp.SerializeToString())
Telemetri = GetMessageClass(
    havuz.FindMessageTypeByName("b40.Telemetri"))

resmi = Telemetri(id=150, sicaklik=-3, ad="EV").SerializeToString()
ben = el.telemetri_kodla(150, -3, "EV")
print("resmi kutuphane:", resmi.hex(" "))
print("elle kodlama   :", ben.hex(" "))
print("ayni mi        :", resmi == ben)
